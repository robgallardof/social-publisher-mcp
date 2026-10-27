"""Exercise the Docker smoke probe's handshake against the real native MCP server."""
import importlib.util
import os
from pathlib import Path
import sys


def test_smoke_probe_waits_for_real_mcp_tool_response(ws):
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location("docker_smoke", root / "scripts/test_docker.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    replies = module.stdio_exchange(
        [sys.executable, "-m", "social_forge.server", "--stdio"],
        module.TOOL,
        env={**os.environ, "SOCIAL_FORGE_ROOT": str(ws)},
    )
    assert replies[1]["result"]["serverInfo"]["name"] == "social-forge"
    assert not replies[2]["result"].get("isError")
    assert replies[2]["result"]["content"]
