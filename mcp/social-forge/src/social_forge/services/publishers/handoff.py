"""Fallback: write a task file so an agent publishes it with computer use / Claude in Chrome / Playwright MCP
(skill `agent-browser-upload`), or a person does it from the phone. Never fails, never posts by itself."""

from __future__ import annotations

from datetime import datetime

from ...config import Settings
from ...domain.platforms import get
from . import Job

SUBTITLES = {"none": "leave platform captions off (no speech, or text already on screen)",
             "auto": "turn ON the platform's automatic captions (Facebook: Compartir step -> Subtitulos)",
             "burned": "already rendered into the video, nothing to do",
             "srt": "upload the .srt next to the video where the platform allows it"}


class Handoff:
    name = "handoff"
    native_schedule = False

    def __init__(self, settings: Settings):
        self.settings = settings

    def check(self) -> str:
        return "ready (writes tasks to content/handoff/ for an agent or a person)"

    def publish(self, job: Job, now: datetime) -> dict:
        d = self.settings.handoff_dir
        d.mkdir(parents=True, exist_ok=True)
        task = d / f"{job.publish_at:%Y-%m-%d_%H%M}-{job.platform}-{job.video.stem}.md"
        title = f"**Title:** {job.copy.title}\n\n" if job.copy.title else ""
        task.write_text(
            f"# Publish on {get(job.platform).name}\n\n"
            f"- **When:** {job.publish_at:%Y-%m-%d %H:%M %Z}\n- **Video:** `{job.video}`\n- **Status:** pending\n\n"
            f"{title}**Caption (paste exactly):**\n\n```\n{job.copy.caption}\n```\n\n"
            f"**Subtitles:** {SUBTITLES[job.copy.subtitles]}\n\n"
            "When done, change Status to `done <url>` and call the `mark_published` tool (MCP social-forge).\n",
            encoding="utf-8")
        return {"status": "handoff", "task": str(task)}
