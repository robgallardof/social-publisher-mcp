"""Workspace settings: config/social.yaml (falls back to social.example.yaml)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .domain import platforms, post
from .domain.schedule import parse_hhmm

ROOT = Path(os.environ.get("SOCIAL_FORGE_ROOT") or Path(__file__).resolve().parents[4])


@dataclass
class Settings:
    root: Path
    timezone: str = "America/Mexico_City"
    post_time: str = "05:00"
    stagger_minutes: int = 0
    mode: str = "at_time"                 # at_time | ahead
    ahead_days: int = 2                   # mode=ahead: how far ahead to upload with a native schedule
    catch_up: bool = True                 # publish overdue videos left in the queue
    max_attempts: int = 3
    default_platforms: list[str] = field(default_factory=lambda: ["tiktok", "instagram", "facebook", "youtube"])
    backends: dict[str, str] = field(default_factory=dict)  # platform -> publisher name
    weekly: dict = field(default_factory=dict)              # per_day, skip_weekdays
    accounts: dict[str, dict] = field(default_factory=dict) # per-backend options (ids, versions...)
    brand: dict = field(default_factory=dict)               # handles on each network, footer label

    @property
    def queue_dir(self) -> Path:
        return self.root / "content" / "queue"

    @property
    def inbox_dir(self) -> Path:
        return self.root / "content" / "inbox"

    @property
    def published_dir(self) -> Path:
        return self.root / "content" / "published"

    @property
    def handoff_dir(self) -> Path:
        return self.root / "content" / "handoff"

    @property
    def secrets_dir(self) -> Path:
        return self.root / "secrets"

    @property
    def analysis_dir(self) -> Path:
        return self.root / "analytics" / "videos"

    @property
    def metrics_csv(self) -> Path:
        return self.root / "analytics" / "metrics.csv"

    @property
    def brand_footer(self) -> post.Brand:
        return post.Brand.from_dict(self.brand)

    def backend_for(self, platform: str) -> str:
        return self.backends.get(platform, "handoff")

    def validate(self) -> None:
        parse_hhmm(self.post_time)
        if self.mode not in ("at_time", "ahead"):
            raise ValueError("mode must be at_time or ahead")
        for p in [*self.default_platforms, *self.backends]:
            platforms.get(p)


def load(root: Path | None = None) -> Settings:
    root = Path(root or ROOT)
    path = root / "config" / "social.yaml"
    if not path.exists():
        path = root / "config" / "social.example.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    settings = Settings(root=root, **(data or {}))
    settings.validate()
    return settings
