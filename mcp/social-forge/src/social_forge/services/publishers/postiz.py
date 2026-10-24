"""Postiz (open-source scheduler, self-hosted or cloud) as a universal backend: it holds the video and
publishes it at the slot time with its own audited app connections, so the PC can be off at 05:00.

Setup: docs/accounts.md#postiz. secrets/postiz.json = {"api_key": "..."}; config accounts.postiz =
{url, integrations: {tiktok: <id>, instagram: <id>, ...}} (ids from `social-forge doctor` / GET /integrations).
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ...config import Settings
from .. import secrets
from . import Job, PublisherError

PROVIDER = {"tiktok": "tiktok", "instagram": "instagram", "facebook": "facebook", "youtube": "youtube"}


class Postiz:
    name = "postiz"
    native_schedule = True

    def __init__(self, settings: Settings, platform: str, http: httpx.Client | None = None):
        self.settings, self.platform = settings, platform
        self.opts = settings.accounts.get("postiz", {})
        self.base = self.opts.get("url", "https://api.postiz.com/public/v1").rstrip("/")
        self.http = http or httpx.Client(timeout=httpx.Timeout(60, read=600))

    def headers(self) -> dict:
        return {"Authorization": secrets.load(self.settings, "postiz", "api_key")["api_key"]}

    def request(self, method: str, path: str, **kw) -> dict | list:
        r = self.http.request(method, f"{self.base}{path}", headers=self.headers(), **kw)
        if r.status_code >= 400:
            raise PublisherError(f"Postiz {r.status_code}: {r.text[:300]}")
        return r.json()

    def integrations(self) -> list[dict]:
        return self.request("GET", "/integrations")

    def check(self) -> str:
        try:
            ids = self.opts.get("integrations", {})
            if not ids.get(self.platform):
                found = ", ".join(f"{i.get('providerIdentifier')}={i.get('id')}" for i in self.integrations())
                return f"set accounts.postiz.integrations.{self.platform}; available: {found}"
            return "ready"
        except (secrets.MissingSecret, PublisherError, httpx.HTTPError) as e:
            return str(e)

    def settings_for(self, job: Job) -> dict:
        c = job.copy
        extra = self.opts.get("settings", {}).get(self.platform, {})
        base = {"__type": PROVIDER[self.platform]}
        if self.platform == "youtube":
            base |= {"title": c.title, "type": c.privacy, "selfDeclaredMadeForKids": "no",
                     "tags": [{"value": t, "label": t} for t in c.tags]}
        elif self.platform == "tiktok":
            base |= {"privacy_level": "PUBLIC_TO_EVERYONE", "duet": True, "stitch": True, "comment": True,
                     "brand_content_toggle": False, "brand_organic_toggle": False,
                     "content_posting_method": "DIRECT_POST"}
        elif self.platform == "instagram":
            base |= {"post_type": "post", "collaborators": []}
        return base | extra

    def publish(self, job: Job, now: datetime) -> dict:
        integration = self.opts.get("integrations", {}).get(self.platform)
        if not integration:
            raise PublisherError(f"accounts.postiz.integrations.{self.platform} is not set")
        with job.video.open("rb") as f:
            media = self.request("POST", "/upload", files={"file": (job.video.name, f, "video/mp4")})
        future = job.publish_at > now
        body = {"type": "schedule" if future else "now",
                "date": job.publish_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "shortLink": False, "tags": [],
                "posts": [{"integration": {"id": integration},
                           "value": [{"content": job.copy.caption,
                                      "image": [{"id": media["id"], "path": media["path"]}]}],
                           "settings": self.settings_for(job)}]}
        created = self.request("POST", "/posts", json=body)
        first = created[0] if isinstance(created, list) and created else created
        return {"status": "scheduled" if future else "published",
                "id": (first or {}).get("postId") or (first or {}).get("id"), "via": "postiz",
                "publish_at": job.publish_at.isoformat() if future else None}
