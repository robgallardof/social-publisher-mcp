"""Pull public metrics of what we published (from the receipts) into analytics/metrics.csv."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import httpx

from ..config import Settings
from ..domain.insights import Metric, summarize
from . import secrets

FIELDS = ["snapshot_at", "platform", "video", "id", "published_at", "views", "likes", "comments", "shares", "saves"]


def published(settings: Settings) -> list[tuple[str, str, str, str]]:
    """(platform, video, id, published_at) for every receipt with a post id."""
    out = []
    for path in settings.published_dir.rglob("*.receipts.json"):
        video = path.name.removesuffix(".receipts.json")
        for platform, r in json.loads(path.read_text(encoding="utf-8")).items():
            if r.get("id") and r.get("status") in ("published", "scheduled"):
                out.append((platform, video, str(r["id"]), r.get("publish_at") or r.get("at")))
    return out


def youtube_stats(settings: Settings, ids: list[str]) -> dict[str, dict]:
    from .publishers.youtube import client

    yt, out = client(settings), {}
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute().get("items", []):
            s = v["statistics"]
            out[v["id"]] = {"views": s.get("viewCount", 0), "likes": s.get("likeCount", 0),
                            "comments": s.get("commentCount", 0)}
    return out


def instagram_stats(settings: Settings, ids: list[str], http: httpx.Client) -> dict[str, dict]:
    token = secrets.load(settings, "meta", "access_token")["access_token"]
    ver = settings.accounts.get("meta", {}).get("graph_version", "v24.0")
    out = {}
    for mid in ids:
        r = http.get(f"https://graph.facebook.com/{ver}/{mid}/insights",
                     params={"metric": "views,likes,comments,shares,saved", "access_token": token})
        if r.status_code < 400:
            vals = {m["name"]: m["values"][0]["value"] for m in r.json().get("data", [])}
            out[mid] = {"views": vals.get("views", 0), "likes": vals.get("likes", 0), "comments": vals.get("comments", 0),
                        "shares": vals.get("shares", 0), "saves": vals.get("saved", 0)}
    return out


def tiktok_stats(settings: Settings, ids: list[str], http: httpx.Client) -> dict[str, dict]:
    token = secrets.load(settings, "tiktok", "access_token")["access_token"]
    out = {}
    for i in range(0, len(ids), 20):
        r = http.post("https://open.tiktokapis.com/v2/video/query/",
                      params={"fields": "id,view_count,like_count,comment_count,share_count"},
                      json={"filters": {"video_ids": ids[i:i + 20]}}, headers={"Authorization": f"Bearer {token}"})
        for v in r.json().get("data", {}).get("videos", []):
            out[str(v["id"])] = {"views": v.get("view_count", 0), "likes": v.get("like_count", 0),
                                 "comments": v.get("comment_count", 0), "shares": v.get("share_count", 0)}
    return out


def pull(settings: Settings) -> dict:
    rows = published(settings)
    http = httpx.Client(timeout=60)
    fetchers = {"youtube": lambda ids: youtube_stats(settings, ids),
                "instagram": lambda ids: instagram_stats(settings, ids, http),
                "tiktok": lambda ids: tiktok_stats(settings, ids, http)}
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    written, errors = 0, {}
    path = settings.metrics_csv
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for platform, fetch in fetchers.items():
            mine = [r for r in rows if r[0] == platform]
            if not mine:
                continue
            try:
                stats = fetch([r[2] for r in mine])
            except Exception as e:  # noqa: BLE001 - one platform failing must not stop the rest
                errors[platform] = str(e)
                continue
            for _, video, pid, at in mine:
                if pid in stats:
                    w.writerow({"snapshot_at": now, "platform": platform, "video": video, "id": pid,
                                "published_at": at, **{k: stats[pid].get(k, 0) for k in FIELDS[5:]}})
                    written += 1
    skipped = sorted({r[0] for r in rows} - set(fetchers))
    return {"rows_written": written, "csv": str(path), "errors": errors,
            "not_supported": skipped and f"{', '.join(skipped)}: read them in the platform's insights (browser)"}


def read(path: Path) -> list[Metric]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [Metric(r["platform"], r["video"], datetime.fromisoformat(r["published_at"]),
                       int(float(r["views"] or 0)), int(float(r["likes"] or 0)), int(float(r["comments"] or 0)),
                       int(float(r["shares"] or 0)), int(float(r["saves"] or 0)))
                for r in csv.DictReader(f) if r.get("published_at")]


def report(settings: Settings) -> dict:
    return summarize(read(settings.metrics_csv))
