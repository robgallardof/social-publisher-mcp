"""Turn a week folder with loose videos into day folders (what to post, how many per day)."""

from __future__ import annotations

from datetime import date

from ..config import Settings
from ..domain import schedule
from . import queue


def plan_week(settings: Settings, today: date, week: str | None = None, apply: bool = False) -> dict:
    week = week or schedule.week_name(today)
    days = schedule.parse_week(week)
    if days is None:
        raise ValueError(f"week must look like 2026-W44, got {week!r}")
    loose = [i for i in queue.scan(settings.queue_dir) if i.day is None and i.week == week]
    already = {d: sum(1 for i in queue.scan(settings.queue_dir) if i.day == d) for d in days}
    future = [d for d in days if d >= today]
    opts = settings.weekly or {}
    per_day = opts.get("per_day")
    by_name = {i.video.name: i for i in loose}
    plan = schedule.distribute(list(by_name), future, per_day, tuple(opts.get("skip_weekdays", ())))
    if per_day:  # respect videos already placed in a day folder
        plan = {d: names[:max(0, per_day - already[d])] for d, names in plan.items()}
    assigned = {n for names in plan.values() for n in names}
    moved = {}
    if apply:
        for d, names in plan.items():
            for n in names:
                moved[n] = str(queue.assign(by_name[n].video, d))
    return {"week": week, "plan": {d.isoformat(): names for d, names in plan.items()},
            "already_in_day_folders": {d.isoformat(): n for d, n in already.items() if n},
            "unassigned": sorted(set(by_name) - assigned), "applied": apply, "moved": moved}
