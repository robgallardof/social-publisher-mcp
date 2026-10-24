from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml

from social_forge import config

TZ = ZoneInfo("America/Mexico_City")


def at(y, mo, d, h=0, mi=0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=TZ)


@pytest.fixture
def ws(tmp_path: Path):
    """A throw-away workspace with a config and an empty queue."""
    (tmp_path / "config").mkdir()
    (tmp_path / "content" / "queue").mkdir(parents=True)
    (tmp_path / "config" / "social.yaml").write_text(yaml.safe_dump({
        "timezone": "America/Mexico_City", "post_time": "05:00",
        "default_platforms": ["tiktok", "youtube"],
        "backends": {"tiktok": "fake_now", "youtube": "fake_sched"}}), encoding="utf-8")
    return tmp_path


def add_video(ws: Path, rel: str, copy: dict | None = None) -> Path:
    video = ws / "content" / "queue" / rel
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"\x00" * 1024)
    if copy is not None:
        video.with_name(video.stem + ".post.yaml").write_text(yaml.safe_dump(copy), encoding="utf-8")
    return video


class FakePublisher:
    calls: list = []

    def __init__(self, name, platform, native, fail=False):
        self.name, self.platform, self.native_schedule, self.fail = name, platform, native, fail

    def check(self):
        return "ready"

    def publish(self, job, now):
        FakePublisher.calls.append((job.video.name, job.platform, job.publish_at, now))
        if self.fail:
            from social_forge.services.publishers import PublisherError
            raise PublisherError("boom")
        return {"status": "scheduled" if job.publish_at > now else "published", "id": f"id-{job.video.stem}"}


def factory(fail_platforms=()):
    def make(name, platform, settings):
        return FakePublisher(name, platform, native=name == "fake_sched", fail=platform in fail_platforms)
    return make


@pytest.fixture
def settings(ws):
    FakePublisher.calls = []
    return config.load(ws)
