"""The daily job: publish (or pre-schedule) everything due. Idempotent: run it as often as you like.

mode=at_time  every video of a day goes out at post_time (05:00) of that day; the PC must be on.
mode=ahead    videos up to `ahead_days` away are uploaded now with the platform's own schedule when the
              backend supports it (YouTube, Facebook, Postiz); the rest still wait for their slot time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from ..config import Settings
from ..domain import post, schedule
from . import queue
from .publishers import Job, Publisher, PublisherError, build

Factory = Callable[[str, str, Settings], Publisher]
FINAL = ("published", "scheduled")


def slot_for(item: queue.Item, index: int, settings: Settings) -> datetime:
    at = schedule.parse_hhmm((item.spec and item.spec.publish_time) or settings.post_time)
    return schedule.slot(item.day, at, settings.timezone, index, settings.stagger_minutes)


def platforms_for(item: queue.Item, settings: Settings) -> list[str]:
    return (item.spec and item.spec.platforms) or settings.default_platforms


def complete(item: queue.Item, settings: Settings) -> bool:
    return all(item.receipts.get(p, {}).get("status") in FINAL for p in platforms_for(item, settings))


def plan(settings: Settings, now: datetime, factory: Factory = build) -> list[dict]:
    """What would happen now, without touching anything (also used by run)."""
    today = now.astimezone(schedule.ZoneInfo(settings.timezone)).date()
    start = today - timedelta(days=30) if settings.catch_up else today
    end = today + timedelta(days=settings.ahead_days if settings.mode == "ahead" else 0)
    items = queue.due(queue.scan(settings.queue_dir), start, end)
    by_day: dict = {}
    actions = []
    for item in items:
        index = by_day.setdefault(item.day, 0)
        by_day[item.day] += 1
        when = slot_for(item, index, settings)
        for platform in platforms_for(item, settings):
            backend = settings.backend_for(platform)
            if item.done(platform):
                continue
            action = {"item": item, "platform": platform, "backend": backend, "at": when, "do": None}
            if item.spec is None or item.spec_error or not item.spec.approved:
                action["do"] = "skip"
                action["why"] = item.spec_error or ("waiting approval" if item.spec else "no copy (.post.yaml)")
            elif item.attempts(platform) >= settings.max_attempts:
                action["do"] = "give_up"
            elif when <= now:
                action["do"] = "publish"
            elif settings.mode == "ahead" and factory(backend, platform, settings).native_schedule:
                action["do"] = "schedule"
            else:
                action["do"] = "wait"
            actions.append(action)
    return actions


def run(settings: Settings, now: datetime, dry_run: bool = False, factory: Factory = build,
        only: str | None = None) -> list[dict]:
    """Execute the plan. `only` limits to one video file name."""
    report = []
    touched: dict[str, queue.Item] = {}
    for a in plan(settings, now, factory):
        item, platform = a["item"], a["platform"]
        if only and item.video.name != only:
            continue
        line = {"video": item.video.name, "day": item.day.isoformat(), "platform": platform,
                "backend": a["backend"], "at": a["at"].isoformat(), "do": a["do"], "why": a.get("why")}
        if a["do"] in ("publish", "schedule"):
            copy = post.render(item.spec, platform, settings.brand_footer)
            problems = post.validate(copy)
            if problems:
                line |= {"do": "skip", "why": "; ".join(problems)}
            elif not dry_run:
                try:
                    receipt = factory(a["backend"], platform, settings).publish(Job(item.video, copy, a["at"]), now)
                except (PublisherError, RuntimeError, OSError, ImportError) as e:
                    receipt = {"status": "failed", "error": str(e)}
                queue.record(item, platform, receipt)
                line["result"] = receipt
                touched[str(item.video)] = item
        report.append(line)
    for item in touched.values():
        if complete(item, settings):
            queue.archive(item, settings.published_dir)
        elif any(item.attempts(p) >= settings.max_attempts and item.receipts[p].get("status") == "failed"
                 for p in item.receipts):
            report.append({"video": item.video.name, "do": "attention",
                           "why": f"reached {settings.max_attempts} failed attempts; see receipts"})
    return report


def mark_published(settings: Settings, video_name: str, platform: str, url: str | None,
                   status: str = "published") -> dict:
    """Close a handoff/manual upload (status published, or scheduled when the platform holds it for the slot)
    and archive the video when every platform is done."""
    if status not in FINAL:
        raise ValueError(f"status must be one of {FINAL}")
    for item in queue.scan(settings.queue_dir):
        if item.video.name == video_name:
            queue.record(item, platform, {"status": status, "url": url, "via": "manual"})
            archived = queue.archive(item, settings.published_dir) if complete(item, settings) else None
            return {"receipts": item.receipts, "archived": str(archived) if archived else None}
    raise FileNotFoundError(f"{video_name} is not in the queue")
