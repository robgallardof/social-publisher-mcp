"""Which day and time each video goes out. Pure: dates in, dates out.

Folder convention under content/queue (any depth, so you can group by week or month):
  2026-10-27/            -> every video inside is published that day
  2026-W44/              -> loose videos are spread over that ISO week by `distribute`
  2026-W44/2026-10-27/   -> same as a dated folder
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

DAY_DIR = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
WEEK_DIR = re.compile(r"^(\d{4})-W(\d{2})$", re.IGNORECASE)


def parse_day(name: str) -> date | None:
    m = DAY_DIR.match(name)
    if not m:
        return None
    try:
        return date(*map(int, m.groups()))
    except ValueError:
        return None


def parse_week(name: str) -> list[date] | None:
    """The seven dates (Mon..Sun) of a `YYYY-Www` folder name."""
    m = WEEK_DIR.match(name)
    if not m:
        return None
    try:
        monday = date.fromisocalendar(int(m[1]), int(m[2]), 1)
    except ValueError:
        return None
    return [monday + timedelta(days=i) for i in range(7)]


def week_name(day: date) -> str:
    y, w, _ = day.isocalendar()
    return f"{y}-W{w:02d}"


def parse_hhmm(value: str) -> time:
    try:
        h, m = value.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        raise ValueError(f"time must be HH:MM, got {value!r}") from None


def distribute(videos: list[str], days: list[date], per_day: int | None = None,
               skip_weekdays: tuple[int, ...] = ()) -> dict[date, list[str]]:
    """Spread videos over the given days in order.

    per_day=None spreads evenly (front-loaded). With per_day=N each day gets up to N and
    whatever does not fit stays unassigned (returned under no key: caller reports it).
    skip_weekdays uses date.weekday() numbers (0=Mon .. 6=Sun).
    """
    usable = [d for d in days if d.weekday() not in skip_weekdays]
    plan: dict[date, list[str]] = {d: [] for d in usable}
    if not usable or not videos:
        return plan
    if per_day is None:
        base, extra = divmod(len(videos), len(usable))
        counts = [base + (i < extra) for i in range(len(usable))]
    else:
        counts = [per_day] * len(usable)
    it = iter(sorted(videos))
    for d, n in zip(usable, counts):
        for _ in range(n):
            nxt = next(it, None)
            if nxt is None:
                return plan
            plan[d].append(nxt)
    return plan


def slot(day: date, at: time, tz: str, index: int = 0, stagger_minutes: int = 0) -> datetime:
    """Aware publish datetime for the index-th video of a day (stagger 0 = all at the same time)."""
    base = datetime.combine(day, at, tzinfo=ZoneInfo(tz))
    return base + timedelta(minutes=stagger_minutes * index)
