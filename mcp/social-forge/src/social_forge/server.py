"""social-forge MCP server: thin wrappers over app.py. Run: uv run social-forge-mcp"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import app

mcp = FastMCP("social-forge")


@mcp.tool()
def queue_status(days: int = 7) -> dict:
    """Videos scheduled for the next `days` (plus overdue ones), how many per day, which lack copy, and new videos
    waiting in content/inbox (analyse them, then move each into a YYYY-MM-DD queue folder)."""
    return app.queue_status(days)


@mcp.tool()
def plan_week(week: str | None = None, apply: bool = False) -> dict:
    """Spread loose videos of a week folder (e.g. 2026-W44) over its remaining days.
    apply=False only shows the plan; apply=True moves them into YYYY-MM-DD folders."""
    return app.plan_week(week, apply)


@mcp.tool()
def check_video(video: str) -> dict:
    """Probe a queued video (duration, resolution) against each target platform's limits."""
    return app.check_video(video)


@mcp.tool()
def write_post(video: str, caption: str, title: str = "", hashtags: list[str] | None = None,
               platforms: list[str] | None = None, overrides: dict | None = None,
               publish_time: str | None = None, approved: bool = True, footer: bool = True,
               subtitles: str = "none", analysis_notes: dict | None = None) -> dict:
    """Save the copy for a queued video (<video>.post.yaml) and return the per-platform preview.
    The brand footer (handles on the other networks) is added automatically unless footer=false.
    subtitles: none | auto (turn on platform captions) | burned (already in the picture) | srt.
    overrides: {platform: {caption?, title?, hashtags?, tags?, privacy?, footer?, subtitles?}}.
    publish_time "HH:MM" overrides 05:00. analysis_notes: what analyze_video found (summary, speech...)."""
    return app.write_post(video, caption, title, hashtags, platforms, overrides, publish_time, approved,
                          footer, subtitles, analysis_notes)


@mcp.tool()
def analyze_video(video: str, language: str = "es") -> dict:
    """Understand a video before writing about it: duration, a contact sheet of 8 frames (open it and look),
    the speech transcript, whether there is speech, and an .srt when there is. Works on inbox, queue,
    library or published videos (name or absolute path). Needs the `analysis` extra for the transcript."""
    return app.analyze_video(video, language)


@mcp.tool()
def make_subtitles(video: str, burn: bool = False, language: str = "es") -> dict:
    """Create an .srt from the speech; burn=true also renders a subtitled MP4 into content/library/ for review
    (the original is never modified)."""
    return app.make_subtitles(video, burn, language)


@mcp.tool()
def brand_info() -> dict:
    """The account's handles per network, the footer each platform will get, and which handles are missing."""
    return app.brand_info()


@mcp.tool()
def preview_post(video: str) -> dict:
    """Final text each platform will receive, its length and blocking problems."""
    return app.preview_post(video)


@mcp.tool()
def publish_due(dry_run: bool = True) -> list[dict]:
    """Publish (or pre-schedule in mode=ahead) everything due now. Always dry_run first and show the plan."""
    return app.publish_due(dry_run)


@mcp.tool()
def publish_now(video: str, dry_run: bool = True) -> list[dict]:
    """Publish one queued video immediately, ignoring its 05:00 slot. Ask the user before dry_run=False."""
    return app.publish_now(video, dry_run)


@mcp.tool()
def mark_published(video: str, platform: str, url: str | None = None, status: str = "published") -> dict:
    """Record a manual/agent upload (handoff) as published, or status="scheduled" when it was scheduled in the
    platform itself; archives the video when all platforms are done."""
    return app.mark_published(video, platform, url, status)


@mcp.tool()
def backends_status() -> dict:
    """Which backend each platform uses and whether it is ready (credentials, login, extras)."""
    return app.backends_status()


@mcp.tool()
def platform_rules() -> str:
    """Duration, caption, title and hashtag limits plus native scheduling per platform."""
    return app.platform_rules()


@mcp.tool()
def pull_metrics() -> dict:
    """Append a metrics snapshot of published videos to analytics/metrics.csv (YouTube, Instagram, TikTok APIs)."""
    return app.pull_metrics()


@mcp.tool()
def insights_report() -> dict:
    """Per-platform medians, engagement, best weekdays, top and bottom videos from analytics/metrics.csv."""
    return app.insights_report()


def _register_agent_files() -> None:
    """Skills become MCP resources and roles become MCP prompts, so any client that installs this server
    gets the playbooks too (not only clients that read .agents/)."""
    import re

    root = app.settings().root / ".agents"
    meta = re.compile(r"^---\n(.*?)\n---\n", re.S)

    def describe(text: str) -> str:
        m = meta.match(text)
        found = re.search(r'description:\s*"?(.*?)"?\s*$', m[1], re.M) if m else None
        return found[1] if found else ""

    def constant(text: str):
        return lambda: text  # no parameters: FastMCP would expose them as arguments

    for skill in sorted(root.glob("skills/*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        mcp.resource(f"skill://{skill.parent.name}", name=skill.parent.name, description=describe(text),
                     mime_type="text/markdown")(constant(text))
    for role in sorted(root.glob("agents/*.md")):
        text = role.read_text(encoding="utf-8")
        mcp.prompt(name=role.stem, description=describe(text))(constant(meta.sub("", text, count=1)))


_register_agent_files()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
