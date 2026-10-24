"""YouTube Shorts through the official Data API v3 (videos.insert, resumable).

Setup: docs/accounts.md#youtube. `social-forge auth youtube` stores secrets/youtube_token.json.
Unverified Google Cloud projects can only upload private videos until the API audit passes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ...config import Settings
from .. import secrets
from . import Job, PublisherError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]


def credentials(settings: Settings):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    path = secrets.path(settings, "youtube_token")
    if not path.exists():
        raise secrets.MissingSecret("YouTube not authorised: run `uv run social-forge auth youtube`")
    creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def authorize(settings: Settings) -> str:
    from google_auth_oauthlib.flow import InstalledAppFlow

    client = secrets.path(settings, "youtube_client_secret")
    if not client.exists():
        raise secrets.MissingSecret("put the OAuth Desktop client JSON at secrets/youtube_client_secret.json")
    creds = InstalledAppFlow.from_client_secrets_file(str(client), SCOPES).run_local_server(port=0)
    secrets.path(settings, "youtube_token").write_text(creds.to_json(), encoding="utf-8")
    return "YouTube authorised"


def client(settings: Settings):
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=credentials(settings), cache_discovery=False)


class YouTubeApi:
    name = "youtube_api"
    native_schedule = True

    def __init__(self, settings: Settings):
        self.settings = settings
        self.opts = settings.accounts.get("youtube", {})

    def check(self) -> str:
        try:
            credentials(self.settings)
            return "ready"
        except ImportError:
            return "install extras: uv sync --extra youtube"
        except Exception as e:  # noqa: BLE001 - doctor reports, never raises
            return str(e)

    def body(self, job: Job, now: datetime) -> dict:
        status = {"selfDeclaredMadeForKids": bool(self.opts.get("made_for_kids", False))}
        # publishAt needs a private video and a time in the future (keep a margin for processing).
        if job.publish_at > now + timedelta(minutes=15):
            status |= {"privacyStatus": "private",
                       "publishAt": job.publish_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        else:
            status["privacyStatus"] = job.copy.privacy
        return {"snippet": {"title": job.copy.title, "description": job.copy.caption, "tags": list(job.copy.tags),
                            "categoryId": str(self.opts.get("category_id", 22)),
                            "defaultLanguage": self.opts.get("language", "es")},
                "status": status}

    def publish(self, job: Job, now: datetime) -> dict:
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        body = self.body(job, now)
        try:
            request = client(self.settings).videos().insert(
                part="snippet,status", body=body,
                media_body=MediaFileUpload(str(job.video), chunksize=8 * 1024 * 1024, resumable=True))
            response = None
            while response is None:
                _, response = request.next_chunk()
        except HttpError as e:
            raise PublisherError(f"YouTube API: {e.reason if hasattr(e, 'reason') else e}") from e
        vid = response["id"]
        return {"status": "scheduled" if "publishAt" in body["status"] else "published", "id": vid,
                "url": f"https://youtube.com/shorts/{vid}", "publish_at": body["status"].get("publishAt")}
