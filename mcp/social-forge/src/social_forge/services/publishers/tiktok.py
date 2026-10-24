"""TikTok through the official Content Posting API (Direct Post, FILE_UPLOAD in chunks).

Until TikTok audits your app every post is forced to SELF_ONLY (private): use `postiz` or `browser`
for public posts meanwhile. Setup: docs/accounts.md#tiktok (secrets/tiktok.json with access_token).
"""

from __future__ import annotations

import math
import time
from datetime import datetime

import httpx

from ...config import Settings
from .. import secrets
from . import Job, PublisherError

API = "https://open.tiktokapis.com/v2"
MB = 1024 * 1024


def chunks(size: int, chunk: int = 10 * MB) -> list[tuple[int, int]]:
    """(start, end_inclusive) ranges following TikTok's rules: <=64 MB in one piece; otherwise
    floor(size/chunk) pieces with the remainder merged into the last one."""
    if size <= 64 * MB:
        return [(0, size - 1)]
    count = max(1, math.floor(size / chunk))
    ranges = [(i * chunk, (i + 1) * chunk - 1) for i in range(count)]
    ranges[-1] = (ranges[-1][0], size - 1)
    return ranges


class TikTokApi:
    name = "tiktok_api"
    native_schedule = False

    def __init__(self, settings: Settings, http: httpx.Client | None = None, sleep=time.sleep):
        self.settings = settings
        self.opts = settings.accounts.get("tiktok", {})
        self.http = http or httpx.Client(timeout=httpx.Timeout(60, read=600))
        self.sleep = sleep

    def headers(self) -> dict:
        token = secrets.load(self.settings, "tiktok", "access_token")["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}

    def post(self, path: str, body: dict) -> dict:
        r = self.http.post(f"{API}{path}", json=body, headers=self.headers())
        data = r.json()
        err = data.get("error", {})
        if r.status_code >= 400 or err.get("code") not in (None, "ok"):
            raise PublisherError(f"TikTok {err.get('code')}: {err.get('message', r.text[:300])}")
        return data.get("data", {})

    def check(self) -> str:
        try:
            info = self.post("/post/publish/creator_info/query/", {})
            return f"ready (@{info.get('creator_username')}, privacy {info.get('privacy_level_options')})"
        except (secrets.MissingSecret, PublisherError, httpx.HTTPError) as e:
            return str(e)

    def publish(self, job: Job, now: datetime) -> dict:
        info = self.post("/post/publish/creator_info/query/", {})
        wanted = self.opts.get("privacy_level", "PUBLIC_TO_EVERYONE")
        options = info.get("privacy_level_options") or [wanted]
        privacy = wanted if wanted in options else options[0]
        size = job.video.stat().st_size
        ranges = chunks(size)
        init = self.post("/post/publish/video/init/", {
            "post_info": {"title": job.copy.caption, "privacy_level": privacy,
                          "disable_comment": bool(self.opts.get("disable_comment", False)),
                          "disable_duet": bool(self.opts.get("disable_duet", False)),
                          "disable_stitch": bool(self.opts.get("disable_stitch", False)),
                          "video_cover_timestamp_ms": int(self.opts.get("cover_ms", 1000))},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                            "chunk_size": ranges[0][1] + 1, "total_chunk_count": len(ranges)}})
        with job.video.open("rb") as f:
            for start, end in ranges:
                f.seek(start)
                r = self.http.put(init["upload_url"], content=f.read(end - start + 1), headers={
                    "Content-Type": "video/mp4", "Content-Range": f"bytes {start}-{end}/{size}"})
                if r.status_code >= 400:
                    raise PublisherError(f"TikTok upload {r.status_code}: {r.text[:200]}")
        for _ in range(40):
            status = self.post("/post/publish/status/fetch/", {"publish_id": init["publish_id"]})
            if status.get("status") == "PUBLISH_COMPLETE":
                ids = status.get("publicaly_available_post_id") or status.get("publicly_available_post_id") or []
                return {"status": "published", "id": str(ids[0]) if ids else init["publish_id"],
                        "privacy": privacy, "url": None}
            if status.get("status") == "FAILED":
                raise PublisherError(f"TikTok publish failed: {status.get('fail_reason')}")
            self.sleep(15)
        return {"status": "published", "id": init["publish_id"], "privacy": privacy,
                "note": "still processing on TikTok; check the app"}
