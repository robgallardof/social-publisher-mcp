"""The agent-facing files stay consistent with the code."""

import re
import subprocess
import sys
from pathlib import Path

import yaml

from social_forge.services.publishers import SUPPORTED

ROOT = Path(__file__).resolve().parents[3]
AGENTS = ROOT / ".agents"


def frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path} has no frontmatter"
    return yaml.safe_load(m[1])


def test_skills_and_agents_have_valid_frontmatter():
    skills = {p.parent.name for p in AGENTS.glob("skills/*/SKILL.md")}
    assert len(skills) == 10
    for p in [*AGENTS.glob("skills/*/SKILL.md"), *AGENTS.glob("agents/*.md")]:
        fm = frontmatter(p)
        expected = p.parent.name if p.name == "SKILL.md" else p.stem
        assert fm["name"] == expected and len(fm["description"]) > 80


def test_roles_only_reference_existing_skills():
    skills = {p.parent.name for p in AGENTS.glob("skills/*/SKILL.md")}
    for role in AGENTS.glob("agents/*.md"):
        section = role.read_text(encoding="utf-8").split("## Skills", 1)[1].split("##", 1)[0]
        for name in re.findall(r"`([a-z-]+)`", section):
            assert name in skills, f"{role.name} cites unknown skill {name}"


def test_mcp_tools_documented_in_skills_exist():
    from social_forge import server

    tools = {n for n in dir(server) if not n.startswith("_")}
    text = " ".join(p.read_text(encoding="utf-8") for p in AGENTS.rglob("*.md"))
    for name in ("queue_status", "plan_week", "write_post", "preview_post", "publish_due", "publish_now",
                 "mark_published", "backends_status", "pull_metrics", "insights_report", "check_video"):
        assert name in tools and name in text


def test_example_config_loads_and_backends_cover_platforms():
    from social_forge import config

    s = config.load(ROOT)  # social.example.yaml when social.yaml is absent
    for platform in s.default_platforms:
        assert platform in SUPPORTED[s.backend_for(platform)]


def test_browser_flows_cover_every_platform():
    flows = yaml.safe_load((ROOT / "config" / "browser_flows.yaml").read_text(encoding="utf-8"))
    assert set(flows) == set(SUPPORTED["browser"])
    allowed = {"goto", "upload", "wait", "wait_for", "click", "fill", "press"}
    for flow in flows.values():
        assert flow["login_url"].startswith("https://")
        assert {s["do"] for s in flow["steps"]} <= allowed


def test_generated_files_are_fresh():
    """Committed generated docs must match the code (client MCP configs are per machine and git-ignored)."""
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync.py"), "--check"], capture_output=True, text=True)
    assert "platforms.md" not in out.stdout, out.stdout
