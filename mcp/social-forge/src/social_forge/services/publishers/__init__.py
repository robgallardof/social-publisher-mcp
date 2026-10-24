"""Publishers: one strategy per way of uploading. Add one = write a class and register it in REGISTRY.

Every publisher takes a Job and returns a receipt dict:
  {"status": "published" | "scheduled" | "handoff" | "failed", "id": ..., "url": ..., "error": ...}
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from ...config import Settings
from ...domain.post import Copy


@dataclass(frozen=True)
class Job:
    video: Path
    copy: Copy
    publish_at: datetime        # aware; in the past or now = publish immediately

    @property
    def platform(self) -> str:
        return self.copy.platform


class Publisher(Protocol):
    name: str
    native_schedule: bool       # can it hold a video and release it at publish_at by itself?

    def publish(self, job: Job, now: datetime) -> dict: ...

    def check(self) -> str:
        """One line: ready, or what is missing to be ready."""
        ...


class PublisherError(RuntimeError):
    pass


def build(name: str, platform: str, settings: Settings) -> Publisher:
    from . import browser, handoff, meta, postiz, tiktok, youtube

    registry = {
        "youtube_api": lambda: youtube.YouTubeApi(settings),
        "meta_api": lambda: meta.MetaApi(settings, platform),
        "tiktok_api": lambda: tiktok.TikTokApi(settings),
        "postiz": lambda: postiz.Postiz(settings, platform),
        "browser": lambda: browser.Browser(settings, platform),
        "handoff": lambda: handoff.Handoff(settings),
    }
    if name not in registry:
        raise ValueError(f"unknown backend {name!r}; use one of {', '.join(registry)}")
    return registry[name]()


SUPPORTED = {
    "youtube_api": ("youtube",),
    "meta_api": ("instagram", "facebook"),
    "tiktok_api": ("tiktok",),
    "postiz": ("tiktok", "instagram", "facebook", "youtube"),
    "browser": ("tiktok", "instagram", "facebook", "youtube"),
    "handoff": ("tiktok", "instagram", "facebook", "youtube"),
}
