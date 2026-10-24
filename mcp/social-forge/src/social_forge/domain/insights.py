"""Turn metric snapshots into decisions. Pure: rows in, summary out."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass(frozen=True)
class Metric:
    platform: str
    video: str
    published_at: datetime
    views: int
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0

    @property
    def interactions(self) -> int:
        return self.likes + self.comments + self.shares + self.saves

    @property
    def engagement(self) -> float:
        return self.interactions / self.views if self.views else 0.0


def latest(rows: list[Metric]) -> list[Metric]:
    """Keep the last snapshot of each (platform, video): rows are appended over time."""
    last: dict[tuple[str, str], Metric] = {}
    for r in rows:
        last[(r.platform, r.video)] = r
    return list(last.values())


def summarize(rows: list[Metric], top: int = 5) -> dict:
    rows = latest(rows)
    by_platform: dict[str, list[Metric]] = defaultdict(list)
    for r in rows:
        by_platform[r.platform].append(r)
    platforms = {}
    for name, items in sorted(by_platform.items()):
        days: dict[int, list[int]] = defaultdict(list)
        for r in items:
            days[r.published_at.weekday()].append(r.views)
        ranked_days = sorted(days.items(), key=lambda kv: median(kv[1]), reverse=True)
        platforms[name] = {
            "videos": len(items),
            "views_total": sum(r.views for r in items),
            "views_median": median(r.views for r in items),
            "engagement_avg": round(mean(r.engagement for r in items), 4),
            "share_rate_avg": round(mean(r.shares / r.views if r.views else 0 for r in items), 4),
            "best_weekdays": [f"{WEEKDAYS[d]} (median {median(v):g} views, n={len(v)})" for d, v in ranked_days[:3]],
        }
    best = sorted(rows, key=lambda r: (r.engagement, r.views), reverse=True)[:top]
    worst = sorted(rows, key=lambda r: (r.views, r.engagement))[:top]
    pick = lambda r: {"platform": r.platform, "video": r.video, "views": r.views,  # noqa: E731
                      "engagement": round(r.engagement, 4), "published": r.published_at.date().isoformat()}
    return {"platforms": platforms, "top": [pick(r) for r in best], "bottom": [pick(r) for r in worst],
            "note": "Fewer than ~10 videos per platform is anecdotal: say so in the report." if any(
                len(v) < 10 for v in by_platform.values()) else ""}
