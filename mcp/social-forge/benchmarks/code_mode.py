"""Reproducible offline comparison. Run from mcp/social-forge; never reads real account credentials."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import platform
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import imageio_ffmpeg
import tiktoken  # benchmark-only: uv run --with tiktoken python benchmarks/code_mode.py
import yaml
from mcp.server.fastmcp import FastMCP

from social_forge import app, config
from social_forge.services import queue
from social_forge.services.code_approvals import Approvals, canonical
from social_forge.services.code_registry import Registry
from social_forge.services.code_sandbox import execute


def tokens(value):
    return len(tiktoken.get_encoding("cl100k_base").encode(canonical(value), disallowed_special=()))


def direct_server(registry):
    """Private benchmark transport for the identical authorized adapters, not shipped MCP tools.

    Legacy tools lack accounts/proposal/approval operations; pretending those are equivalent would skew results.
    """
    mcp = FastMCP("benchmark-direct")
    for name, capability in registry.capabilities.items():
        def make(name, capability):
            def call(**kwargs) -> dict:
                return registry.dispatch(name, kwargs)
            call.__signature__ = inspect.signature(capability.handler)
            call.__annotations__ = dict(capability.handler.__annotations__)
            # FastMCP resolves annotations in the function module, so use evaluated annotations.
            from typing import get_type_hints
            hints = get_type_hints(capability.handler)
            call.__signature__ = call.__signature__.replace(parameters=[
                p.replace(annotation=hints[p.name]) for p in call.__signature__.parameters.values()
            ], return_annotation=dict)
            call.__annotations__ = {**hints, "return": dict}
            return call
        mcp.tool(name=name.replace(".", "_"), description=capability.description)(make(name, capability))
    return mcp


async def run(args):
    rows = []
    with tempfile.TemporaryDirectory(prefix="code-benchmark-") as temporary:
        root = Path(temporary)
        (root / "config").mkdir()
        (root / "config" / "social.yaml").write_text(yaml.safe_dump({
            "default_platforms": ["tiktok", "instagram", "youtube"],
            "backends": {"tiktok": "tiktok_api", "instagram": "meta_api", "youtube": "youtube_api"},
            "code_mode": {"deno": args.deno},
        }), encoding="utf-8")
        settings = config.load(root)
        video = settings.queue_dir / "2026-11-03" / "fixture.mp4"
        video.parent.mkdir(parents=True)
        await asyncio.to_thread(subprocess.run, [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", "color=c=black:s=1080x1920:d=4", "-pix_fmt", "yuv420p", str(video)],
                       check=True, stdin=subprocess.DEVNULL)
        rel = video.relative_to(settings.queue_dir).as_posix()
        draft = {"caption": "Offline fixture", "title": "Fixture", "platforms": settings.default_platforms}
        from social_forge.domain.post import PostSpec
        queue.save_spec(video, PostSpec(**draft, approved=False))
        registry = Registry(settings)
        server = direct_server(registry)
        # Capture actual additive MCP catalog and actual legacy operations separately.
        from social_forge import server as shipped
        with patch.object(app, "settings", return_value=settings), patch.object(shipped, "mcp", FastMCP("code-only")):
            shipped._register_code_mode()
            code_tools = [t.model_dump(exclude_none=True) for t in await shipped.mcp.list_tools()]
        legacy_tools = [t.model_dump(exclude_none=True) for t in await shipped.mcp.list_tools()
                        if t.name not in ("code_search", "code_execute")]
        direct_tools = [t.model_dump(exclude_none=True) for t in await server.list_tools()]
        proposal = registry.dispatch("posts.propose", {"video": rel, "draft": draft})
        Approvals(settings).approve(proposal["proposal_id"], proposal["digest"])
        cases = [
            ("configured_accounts", [("accounts.list", {})]),
            ("three_provider_requirements", [("accounts.capabilities", {"platform": p}) for p in settings.default_platforms]),
            ("three_provider_media_validation", [("media.inspect", {"video": rel, "targets": settings.default_platforms})]),
            ("multi_platform_proposal", [("posts.preview", {"video": rel, "draft": draft}),
                                         ("posts.propose", {"video": rel, "draft": draft})]),
            ("approved_schedule", [("schedule.create", {"proposal_id": proposal["proposal_id"]})]),
            ("cached_analytics", [("analytics.summary", {})]),
        ]
        # Proposal scenario must precede activation; repeated proposals do not change queue state.
        for scenario, operations in cases:
            samples = {"direct": [], "code": []}
            correctness = []
            search = registry.search(" ".join(name for name, _ in operations), limit=5)
            code = "const result=[];\n" + "\n".join(
                f"result.push(await social.{name}({canonical(parameters)}));" for name, parameters in operations
            ) + "\nreturn result;"
            d_tokens, c_tokens = [], []
            for repeat in range(args.repeats):
                direct_results = []
                started = time.perf_counter()
                for name, parameters in operations:
                    content = await server.call_tool(name.replace(".", "_"), parameters)
                    structured = json.loads(content[0].text)
                    direct_results.append(structured)
                samples["direct"].append((time.perf_counter() - started) * 1000)
                started = time.perf_counter()
                result = await execute(settings, code, read_only=scenario not in ("multi_platform_proposal", "approved_schedule"))
                samples["code"].append((time.perf_counter() - started) * 1000)
                code_results = result["result"]
                # Proposal IDs are intentionally unique; compare immutable semantic snapshot/preview fields.
                def comparable(value):
                    return [{k: v for k, v in item.items() if k != "proposal_id"} for item in value]
                correctness.append(comparable(direct_results) == comparable(code_results))
                d_tokens.append(tokens(direct_tools) + tokens(operations) + tokens(direct_results))
                c_tokens.append(tokens(code_tools) + tokens(search) + tokens({"code": code}) + tokens(result))
            rows.append({"scenario": scenario, "correct_results": all(correctness),
                         "direct_median_ms": round(statistics.median(samples["direct"]), 3),
                         "code_median_ms": round(statistics.median(samples["code"]), 3),
                         "direct_model_visible_tokens": round(statistics.mean(d_tokens)),
                         "code_selected_tools_visible_tokens": round(statistics.mean(c_tokens)),
                         "code_actual_additive_visible_tokens": round(statistics.mean(c_tokens))
                         + tokens(legacy_tools + code_tools) - tokens(code_tools),
                         "direct_round_trips": len(operations), "code_round_trips_including_search": 2,
                         "code_cpu_ms_last": result["metrics"]["cpu_ms"],
                         "code_sampled_peak_rss_bytes_last": result["metrics"]["peak_rss_bytes"],
                         "provider_api_requests": 0, "errors": sum(not ok for ok in correctness)})
        startups = [(await execute(settings, "return null"))["metrics"] for _ in range(args.repeats)]
        # Genuine existing direct MCP operations, with the same fixture and no provider calls.
        legacy_samples = {}
        with patch.object(app, "settings", return_value=settings):
            for name, parameters in [("brand_info", {}), ("platform_rules", {}), ("check_video", {"video": video.name}),
                                     ("preview_post", {"video": video.name}), ("insights_report", {})]:
                values = []
                for _ in range(args.repeats):
                    started = time.perf_counter()
                    await shipped.mcp.call_tool(name, parameters)
                    values.append((time.perf_counter() - started) * 1000)
                legacy_samples[name] = round(statistics.median(values), 3)
        deno_version = await asyncio.to_thread(subprocess.check_output, [args.deno, "--version"], text=True)
        result = {
            "environment": {"os": platform.platform(), "python": platform.python_version(),
                            "deno": deno_version.splitlines()[0]},
            "methodology": {"repeats": args.repeats, "tokenizer": "cl100k_base", "transport": "in-process FastMCP call_tool",
                            "provider_latency": "offline; zero provider requests, real ffmpeg fixture",
                            "baseline": "private direct MCP harness over identical authorized capability adapters",
                            "legacy_limits": "Legacy tools have no equivalent account/proposal/approval operations; timings reported separately.",
                            "visible_tokens": "serialized schema + arguments + result; code includes discovery, no actual LLM conversation",
                            "not_measured": ["real provider latency", "network MCP transport", "model reasoning tokens",
                                             "host Python CPU/RSS", "cross-platform runtime comparison", "paid infrastructure"]},
            "schema_tokens": {"existing_legacy_catalog": tokens(legacy_tools), "equivalent_direct_harness": tokens(direct_tools),
                              "code_tools_only": tokens(code_tools), "actual_additive_catalog": tokens(legacy_tools + code_tools)},
            "sandbox_null_median_ms": round(statistics.median(m["duration_ms"] for m in startups), 3),
            "existing_direct_median_ms": legacy_samples, "scenarios": rows,
        }
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        if not all(row["correct_results"] for row in rows):
            raise SystemExit("benchmark correctness check failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deno", default="deno")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", default="../../docs/benchmarks/code-mode-windows.json")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 100:
        parser.error("repeats must be 1..100")
    asyncio.run(run(args))
