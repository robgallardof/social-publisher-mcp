"""The video folder: discover what is scheduled, its copy and what was already published."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

from ..domain import schedule
from ..domain.platforms import VIDEO_EXTENSIONS
from ..domain.post import PostSpec


@dataclass
class Item:
    video: Path
    day: date | None              # None = loose in a week folder, not yet assigned
    week: str | None = None
    spec: PostSpec | None = None
    spec_error: str | None = None
    receipts: dict[str, dict] = field(default_factory=dict)  # platform -> receipt

    @property
    def sidecar(self) -> Path:
        return sidecar_path(self.video)

    @property
    def receipts_path(self) -> Path:
        return self.video.with_name(self.video.name + ".receipts.json")

    def done(self, platform: str) -> bool:
        return self.receipts.get(platform, {}).get("status") in ("published", "scheduled", "handoff")

    def attempts(self, platform: str) -> int:
        return int(self.receipts.get(platform, {}).get("attempts", 0))

    def summary(self) -> dict:
        return {"video": str(self.video), "day": self.day and self.day.isoformat(), "week": self.week,
                "has_copy": self.spec is not None, "copy_error": self.spec_error,
                "receipts": {p: r.get("status") for p, r in self.receipts.items()}}


def sidecar_path(video: Path) -> Path:
    return video.with_name(video.stem + ".post.yaml")


def is_video(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def load_item(video: Path, day: date | None, week: str | None = None) -> Item:
    item = Item(video, day, week)
    if item.sidecar.exists():
        try:
            item.spec = PostSpec.from_dict(yaml.safe_load(item.sidecar.read_text(encoding="utf-8")))
        except (ValueError, TypeError, yaml.YAMLError) as e:
            item.spec_error = str(e)
    if item.receipts_path.exists():
        item.receipts = json.loads(item.receipts_path.read_text(encoding="utf-8"))
    return item


def scan(queue_dir: Path) -> list[Item]:
    """Every video in the queue, dated by its nearest YYYY-MM-DD ancestor (or loose in a week)."""
    items = []
    for video in sorted(p for p in queue_dir.rglob("*") if is_video(p)):
        day, week = None, None
        for parent in video.relative_to(queue_dir).parents:
            name = parent.name
            day = day or schedule.parse_day(name)
            if schedule.parse_week(name):
                week = week or name
        if day or week:
            items.append(load_item(video, day, week))
    return items


def due(items: list[Item], start: date, end: date) -> list[Item]:
    return sorted((i for i in items if i.day and start <= i.day <= end), key=lambda i: (i.day, i.video.name))


def save_spec(video: Path, spec: PostSpec) -> Path:
    path = sidecar_path(video)
    path.write_text(yaml.safe_dump(spec.to_dict(), allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    return path


def record(item: Item, platform: str, receipt: dict) -> None:
    prev = item.receipts.get(platform, {})
    receipt = {**receipt, "attempts": prev.get("attempts", 0) + 1, "at": datetime.now().astimezone().isoformat()}
    item.receipts[platform] = receipt
    item.receipts_path.write_text(json.dumps(item.receipts, indent=2, ensure_ascii=False), encoding="utf-8")


def companions(video: Path) -> list[Path]:
    return [p for p in (video, sidecar_path(video), video.with_name(video.name + ".receipts.json")) if p.exists()]


def archive(item: Item, dest_root: Path) -> Path:
    """Move a finished video, its copy and receipts to <dest_root>/<day>/."""
    dest = dest_root / (item.day.isoformat() if item.day else "undated")
    dest.mkdir(parents=True, exist_ok=True)
    for path in companions(item.video):
        shutil.move(str(path), dest / path.name)
    return dest / item.video.name


def assign(video: Path, day: date) -> Path:
    """Move a loose week video into its day folder (inside the same week folder)."""
    dest = video.parent / day.isoformat()
    dest.mkdir(exist_ok=True)
    for path in companions(video):
        shutil.move(str(path), dest / path.name)
    return dest / video.name
