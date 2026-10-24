"""Instagram Reels and Facebook Page Reels through the official Graph API (resumable upload from disk).

Instagram: POST /{ig-id}/media (REELS, resumable) -> rupload ig-api-upload -> poll status_code -> media_publish.
           No publish time in the API: the runner calls it at the slot time.
Facebook:  POST /{page-id}/video_reels start -> rupload video-upload -> finish (PUBLISHED or SCHEDULED).
Setup: docs/accounts.md#meta (Facebook Login for Business, Instagram Business account linked to the Page).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

import httpx

from ...config import Settings
from .. import secrets
from . import Job, PublisherError

GRAPH = "https://graph.facebook.com"
RUPLOAD = "https://rupload.facebook.com"


class MetaApi:
    name = "meta_api"

    def __init__(self, settings: Settings, platform: str, http: httpx.Client | None = None, sleep=time.sleep):
        self.settings, self.platform = settings, platform
        self.opts = settings.accounts.get("meta", {})
        self.version = self.opts.get("graph_version", "v24.0")
        self.http = http or httpx.Client(timeout=httpx.Timeout(60, read=600))
        self.sleep = sleep
        self.native_schedule = platform == "facebook"

    # -- helpers -------------------------------------------------------------------------------
    def token(self) -> str:
        key = "page_access_token" if self.platform == "facebook" else "access_token"
        return secrets.load(self.settings, "meta", key)[key]

    def target_id(self) -> str:
        key = "page_id" if self.platform == "facebook" else "ig_user_id"
        if not self.opts.get(key):
            raise secrets.MissingSecret(f"config accounts.meta.{key} is empty")
        return str(self.opts[key])

    def call(self, method: str, url: str, **kw) -> dict:
        r = self.http.request(method, url, **kw)
        data = r.json() if r.content else {}
        if r.status_code >= 400 or "error" in data:
            err = data.get("error", {})
            raise PublisherError(f"Meta {r.status_code}: {err.get('message', r.text[:300])}")
        return data

    def upload(self, url: str, job: Job, token: str) -> None:
        data = job.video.read_bytes()
        self.call("POST", url, content=data,
                  headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))})

    def check(self) -> str:
        try:
            self.token(), self.target_id()
            return "ready"
        except secrets.MissingSecret as e:
            return str(e)

    # -- publish -------------------------------------------------------------------------------
    def publish(self, job: Job, now: datetime) -> dict:
        return self._facebook(job, now) if self.platform == "facebook" else self._instagram(job)

    def _instagram(self, job: Job) -> dict:
        token, ig = self.token(), self.target_id()
        base = f"{GRAPH}/{self.version}"
        params = {"media_type": "REELS", "upload_type": "resumable", "caption": job.copy.caption,
                  "share_to_feed": str(self.opts.get("share_to_feed", True)).lower(), "access_token": token}
        container = self.call("POST", f"{base}/{ig}/media", data=params)["id"]
        self.upload(f"{RUPLOAD}/ig-api-upload/{self.version}/{container}", job, token)
        for _ in range(30):  # up to ~10 min of processing
            status = self.call("GET", f"{base}/{container}", params={"fields": "status_code,status",
                                                                     "access_token": token})
            code = status.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                raise PublisherError(f"Instagram processing {code}: {status.get('status', '')}")
            self.sleep(20)
        else:
            raise PublisherError("Instagram processing timed out; container " + container)
        media = self.call("POST", f"{base}/{ig}/media_publish", data={"creation_id": container, "access_token": token})
        link = self.call("GET", f"{base}/{media['id']}", params={"fields": "permalink", "access_token": token})
        return {"status": "published", "id": media["id"], "url": link.get("permalink")}

    def _facebook(self, job: Job, now: datetime) -> dict:
        token, page = self.token(), self.target_id()
        url = f"{GRAPH}/{self.version}/{page}/video_reels"
        start = self.call("POST", url, data={"upload_phase": "start", "access_token": token})
        vid = start["video_id"]
        self.upload(start.get("upload_url") or f"{RUPLOAD}/video-upload/{self.version}/{vid}", job, token)
        finish = {"upload_phase": "finish", "video_id": vid, "description": job.copy.caption, "access_token": token}
        scheduled = job.publish_at > now + timedelta(minutes=11)
        if scheduled:
            finish |= {"video_state": "SCHEDULED", "scheduled_publish_time": str(int(job.publish_at.timestamp()))}
        else:
            finish["video_state"] = "PUBLISHED"
        self.call("POST", url, data=finish)
        return {"status": "scheduled" if scheduled else "published", "id": vid,
                "url": f"https://www.facebook.com/reel/{vid}",
                "publish_at": job.publish_at.isoformat() if scheduled else None}
