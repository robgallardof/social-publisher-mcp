"""Dedicated deny-all Deno process. Stdio is an untrusted protocol, never an authorization boundary."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

from ..domain.code_mode import CodeModeError, CodeModeSettings
from .code_registry import Registry

_slots = threading.BoundedSemaphore(2)  # process-wide limit, also across independent asyncio event loops


def runtime(limits):
    path = shutil.which(limits.deno)
    if not path or Path(path).suffix.lower() in (".cmd", ".bat", ".ps1"):
        raise CodeModeError("deno_executable_required")
    try:
        import psutil
    except ImportError:
        raise CodeModeError("psutil_dependency_required") from None
    # No shell, no user-supplied flags. Old/unsupported Deno fails closed at process startup.
    check = subprocess.run([path, "--version"], env=clean_env(), capture_output=True, timeout=5, check=False)
    if check.returncode or not check.stdout.startswith(b"deno 2."):
        raise CodeModeError("deno_2_required")
    return path, psutil


def clean_env():
    # Explicit allowlist: DENO_V8_FLAGS, DENO_DIR, proxy settings and OAuth secrets are never inherited.
    return {"DENO_NO_UPDATE_CHECK": "1", "NO_COLOR": "1",
            **{key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR") if key in os.environ}}


async def execute(settings, code: str, *, read_only: bool = True) -> dict:
    limits = CodeModeSettings.from_dict(settings.code_mode)
    if not isinstance(code, str) or len(code.encode()) > limits.max_code_bytes:
        raise CodeModeError("code_size_limit")
    if not _slots.acquire(blocking=False):
        raise CodeModeError("execution_concurrency_limit")
    execution_id = uuid.uuid4().hex
    registry = Registry(settings, execution_id)
    permissions = {c.permission for c in registry.capabilities.values() if not read_only or c.effect == "read"}
    started = time.perf_counter()
    process = None
    tasks = set()
    peak_rss = 0
    cpu_ms = 0
    calls = []
    status = "failed"
    try:
        path, psutil = await asyncio.to_thread(runtime, limits)
        with tempfile.TemporaryDirectory(prefix="social-code-") as directory:
            args = [path, "run", "--quiet", "--no-prompt", "--no-config", "--no-npm", "--no-remote",
                    "--no-code-cache", "--deny-read", "--deny-write", "--deny-net", "--deny-env",
                    "--deny-run", "--deny-ffi", "--deny-sys", "--deny-import",
                    f"--v8-flags=--max-old-space-size={max(16, limits.memory_mb // 2)}",
                    str(Path(__file__).with_name("code_worker.js"))]
            process = await asyncio.create_subprocess_exec(
                *args, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL, env=clean_env(), cwd=directory,
                limit=limits.max_output_bytes + 1)
            observed = psutil.Process(process.pid)
            writer_lock = asyncio.Lock()
            total_bytes = 0
            response_bytes = 0
            seen = set()

            async def send(value):
                nonlocal response_bytes
                data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode() + b"\n"
                if "code" not in value:
                    response_bytes += len(data)
                if response_bytes > limits.max_output_bytes:
                    raise CodeModeError("output_limit")
                async with writer_lock:
                    process.stdin.write(data)
                    await process.stdin.drain()

            async def monitor():
                nonlocal peak_rss, cpu_ms
                while process.returncode is None:
                    try:
                        peak_rss = max(peak_rss, observed.memory_info().rss)
                        times = observed.cpu_times()
                        cpu_ms = (times.user + times.system) * 1000
                    except psutil.NoSuchProcess:
                        return
                    if peak_rss > limits.memory_mb * 1024 * 1024:
                        raise CodeModeError("memory_limit")
                    if cpu_ms > limits.cpu_ms:
                        raise CodeModeError("cpu_limit")
                    await asyncio.sleep(0.01)

            async def invoke(message):
                try:
                    value = await asyncio.to_thread(registry.dispatch, message["name"], message["arguments"],
                                                    permissions=permissions)
                    response = {"id": message["id"], "ok": True, "result": value}
                    calls.append({"name": message["name"], "status": "ok"})
                except CodeModeError as error:
                    response = {"id": message["id"], "ok": False, "error": error.code}
                    calls.append({"name": message["name"] if message["name"] in registry.capabilities else "unknown",
                                  "status": error.code})
                await send(response)

            async def protocol():
                nonlocal total_bytes
                await send({"code": code, "max_concurrency": limits.max_concurrency,
                            "capabilities": list(registry.capabilities)})
                while True:
                    try:
                        raw = await process.stdout.readline()
                    except ValueError:
                        raise CodeModeError("output_limit") from None
                    total_bytes += len(raw)
                    if not raw:
                        raise CodeModeError("sandbox_failed")
                    if total_bytes > limits.max_output_bytes:
                        raise CodeModeError("output_limit")
                    try:
                        message = json.loads(raw)
                    except (ValueError, UnicodeError):
                        raise CodeModeError("invalid_bridge_message") from None
                    if not isinstance(message, dict):
                        raise CodeModeError("invalid_bridge_message")
                    if message.get("type") == "call":
                        if (set(message) != {"type", "id", "name", "arguments"}
                                or type(message["id"]) is not int or not isinstance(message["name"], str)):
                            raise CodeModeError("invalid_bridge_message")
                        if message["id"] in seen or len(seen) >= limits.max_calls:
                            raise CodeModeError("call_limit")
                        seen.add(message["id"])
                        active = [t for t in tasks if not t.done()]
                        if len(active) >= limits.max_concurrency:
                            raise CodeModeError("concurrency_limit")
                        tasks.add(asyncio.create_task(invoke(message)))
                    elif message.get("type") == "result":
                        if any(not t.done() for t in tasks):
                            raise CodeModeError("unawaited_operations")
                        return message.get("result")
                    else:
                        raise CodeModeError("javascript_error")

            watcher = asyncio.create_task(monitor())
            protocol_task = asyncio.create_task(protocol())
            try:
                remaining = max(0.001, limits.timeout_ms / 1000 - (time.perf_counter() - started))
                async with asyncio.timeout(remaining):
                    while not protocol_task.done():
                        pending_tasks = [t for t in tasks if not t.done()]
                        for task in tasks:
                            if task.done() and task.exception():
                                raise task.exception()
                        done, _ = await asyncio.wait([watcher, protocol_task, *pending_tasks],
                                                     return_when=asyncio.FIRST_COMPLETED)
                        for task in done:
                            if task.exception():
                                raise task.exception()
                        # Completed invocations must stay in tasks for exception inspection, but not in wait().
                        if watcher.done() and not protocol_task.done():
                            await protocol_task
                        if not protocol_task.done():
                            await asyncio.sleep(0.001)
                    value = protocol_task.result()
            finally:
                watcher.cancel()
                protocol_task.cancel()
                await asyncio.gather(watcher, protocol_task, return_exceptions=True)
                # Windows holds the child's working directory open until process termination.
                if process.returncode is None:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                await process.wait()
            status = "ok"
            return {"execution_id": execution_id, "status": status, "result": value, "calls": calls,
                    "metrics": {"duration_ms": round((time.perf_counter() - started) * 1000, 2),
                                "peak_rss_bytes": peak_rss, "cpu_ms": cpu_ms}}
    except TimeoutError:
        status = "execution_timeout"
        error = CodeModeError("execution_timeout")
        error.details = {"execution_id": execution_id, "calls": calls}
        raise error from None
    except (OSError, ValueError) as error:
        if isinstance(error, CodeModeError):
            status = error.code
            error.details = {"execution_id": execution_id, "calls": calls}
            raise
        status = "sandbox_failed"
        raise CodeModeError("sandbox_failed") from None
    except asyncio.CancelledError:
        status = "cancelled"
        raise
    except Exception:  # noqa: BLE001 - boundary must sanitize runtime/native error details
        status = "sandbox_failed"
        raise CodeModeError("sandbox_failed") from None
    finally:
        if process is not None and process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
        # Host writes already admitted by the bridge finish under their workspace lock. They never publish.
        # Await them even on cancellation, rather than orphaning state-changing background threads.
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        try:
            registry.approvals.audit(execution_id, "sandbox", status, (time.perf_counter() - started) * 1000)
        finally:
            _slots.release()
