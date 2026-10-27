"""Real test of the Docker image and the Compose services (standard library only).

Builds the image, speaks MCP over stdio with `docker run -i`, checks that the image holds
no personal data, runs the one-shot CLI service, and starts Compose over HTTP on a free
port with a token, calling a real tool. Uses a throw-away workspace (config + .agents copy),
never your videos or secrets. Cleans up containers and temp files on exit.

    python scripts/test_docker.py                 # default image (EXTRAS=youtube)
    python scripts/test_docker.py --extras youtube,analysis
"""

import argparse
import json
import os
import queue
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "social-forge:local"
SERVER_NAME = "social-forge"
PREFIX = "SOCIAL_FORGE"  # compose variables: <PREFIX>_MCP_TOKEN, _PORT, _WORKSPACE, _USER
WORKSPACE_COPY = [".agents"]
TOOL = ("platform_rules", {})
FORBIDDEN_IN_IMAGE = ["social.yaml", "secrets", "content", ".profiles"]
SOCIAL_YAML = """timezone: America/Mexico_City
post_time: "05:00"
default_platforms: [tiktok]
backends: {tiktok: handoff}
"""


def run(*args, env=None, input=None, timeout=600):
    out = subprocess.run(args, env=env, input=input, text=True, capture_output=True, timeout=timeout,
                         encoding="utf-8")
    if out.returncode:
        raise RuntimeError(f"failed {' '.join(args)}:\n{out.stdout}\n{out.stderr}")
    return out.stdout


def rpc(url, token, message, session=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "Authorization": f"Bearer {token}"}
    if session:
        headers.update({"Mcp-Session-Id": session, "MCP-Protocol-Version": "2025-11-25"})
    req = urllib.request.Request(url, json.dumps(message).encode(), headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode()
        if "text/event-stream" in resp.headers.get("Content-Type", ""):
            data = next((line[5:].strip() for line in data.splitlines()
                         if line.startswith("data:") and line[5:].strip()), "")
        return (json.loads(data) if data else None), resp.headers.get("Mcp-Session-Id")


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "docker-smoke", "version": "1"}}}
INITIALIZED = {"jsonrpc": "2.0", "method": "notifications/initialized"}


def stdio_exchange(command, tool, *, env=None, timeout=30):
    """Complete each real MCP request before closing stdin and ending the session."""
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errors:
        child = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=errors, text=True, encoding="utf-8")
        messages = queue.Queue()

        def read():
            try:
                for line in child.stdout:
                    messages.put(line)
            finally:
                messages.put(None)

        reader = threading.Thread(target=read, daemon=True)
        reader.start()

        def send(message):
            child.stdin.write(json.dumps(message) + "\n")
            child.stdin.flush()

        def response(request_id):
            deadline = time.monotonic() + timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"MCP did not answer request {request_id}")
                try:
                    line = messages.get(timeout=remaining)
                except queue.Empty as error:
                    raise TimeoutError(f"MCP did not answer request {request_id}") from error
                if line is None:
                    errors.seek(0)
                    raise RuntimeError(f"MCP exited before request {request_id}: {errors.read()[-4000:]}")
                message = json.loads(line)
                if message.get("id") == request_id:
                    if "error" in message:
                        raise RuntimeError(f"MCP request {request_id} failed: {message['error']}")
                    return message

        try:
            send(INIT)
            initialized = response(1)
            send(INITIALIZED)
            send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                  "params": {"name": tool[0], "arguments": tool[1]}})
            return {1: initialized, 2: response(2)}
        finally:
            try:
                child.stdin.close()
            except BrokenPipeError:
                pass
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
            reader.join(timeout=5)
            child.stdout.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extras", default="youtube")
    extras = parser.parse_args().extras
    run("docker", "build", "--build-arg", f"EXTRAS={extras}", "-t", IMAGE, str(ROOT))
    print(f"ok  build (EXTRAS={extras})")

    listing = run("docker", "run", "--rm", "--entrypoint", "sh", IMAGE, "-c",
                  "find / -xdev \\( -path /proc -o -path /sys \\) -prune -o -print 2>/dev/null; true")
    for name in FORBIDDEN_IN_IMAGE:
        hits = [p for p in listing.splitlines() if p.endswith("/" + name) and "/site-packages/" not in p]
        assert not hits, f"image contains {name}: {hits}"
    print("ok  image holds no personal data")

    with tempfile.TemporaryDirectory(prefix="mcp-docker-") as tmp:
        work = Path(tmp)
        for name in WORKSPACE_COPY:
            if (ROOT / name).exists():
                shutil.copytree(ROOT / name, work / name)
        (work / "config").mkdir()
        (work / "content" / "queue").mkdir(parents=True)
        (work / "config" / "social.yaml").write_text(SOCIAL_YAML, encoding="utf-8")
        os.chmod(work, 0o777)
        user = f"{os.getuid()}:{os.getgid()}" if hasattr(os, "getuid") else "10001:10001"
        mount = f"{work}:/workspace"

        replies = stdio_exchange(["docker", "run", "--rm", "-i", "--user", user, "-v", mount, IMAGE], TOOL)
        assert replies[1]["result"]["serverInfo"]["name"] == SERVER_NAME, replies[1]
        assert not replies[2]["result"].get("isError"), replies[2]
        print("ok  stdio: initialize + tools/call", TOOL[0])
        if "analysis" in extras:
            run("docker", "run", "--rm", "--entrypoint", "python", IMAGE, "-c", "import faster_whisper")
            print("ok  analysis extra importable")

        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        token = secrets.token_hex(32)
        project = f"smoke{secrets.token_hex(3)}"
        env = dict(os.environ, **{f"{PREFIX}_MCP_TOKEN": token, f"{PREFIX}_PORT": str(port),
                                  f"{PREFIX}_WORKSPACE": str(work), f"{PREFIX}_USER": user,
                                  f"{PREFIX}_EXTRAS": extras})
        compose = ["docker", "compose", "-p", project, "-f", str(ROOT / "compose.yaml")]
        try:
            status = run(*compose, "run", "--rm", "cli", "status", env=env, timeout=300)
            json.loads(status)
            print("ok  compose cli: status")
            run(*compose, "up", "-d", "--wait", "social-forge", env=env, timeout=300)
            url = f"http://127.0.0.1:{port}"
            with urllib.request.urlopen(url + "/healthz", timeout=10) as r:
                assert r.status == 200
            try:
                rpc(url + "/mcp", "x" * 64, INIT)
                raise AssertionError("accepted a wrong token")
            except urllib.error.HTTPError as e:
                assert e.code == 401, e.code
            init, session = rpc(url + "/mcp", token, INIT)
            assert init["result"]["serverInfo"]["name"] == SERVER_NAME
            rpc(url + "/mcp", token, INITIALIZED, session)
            tools, _ = rpc(url + "/mcp", token, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session)
            names = {t["name"] for t in tools["result"]["tools"]}
            assert TOOL[0] in names, names
            called, _ = rpc(url + "/mcp", token, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                                  "params": {"name": TOOL[0], "arguments": TOOL[1]}}, session)
            assert not called["result"].get("isError"), called
            print(f"ok  compose HTTP on port {port}: token, {len(names)} tools, {TOOL[0]}")
        finally:
            subprocess.run([*compose, "down", "--remove-orphans"], env=env, capture_output=True, timeout=120)
            time.sleep(0.5)
    print("all ok")


if __name__ == "__main__":
    main()
