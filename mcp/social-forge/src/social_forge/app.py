"""Use cases shared by the MCP server and the CLI (one place, two thin front-ends)."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from . import config
from .domain import platforms, post
from .services import analysis, analytics, media, planner, queue, runner
from .services.publishers import SUPPORTED, build


def settings():
    return config.load()


def now() -> datetime:
    return datetime.now().astimezone()


def find(video: str) -> queue.Item:
    s = settings()
    for item in queue.scan(s.queue_dir):
        if item.video.name == video or str(item.video) == video or item.video == Path(video):
            return item
    raise FileNotFoundError(f"{video} is not in content/queue (dated YYYY-MM-DD or YYYY-Www folder)")


def locate(video: str) -> Path:
    """A video anywhere in content/ (inbox, queue, library, published) or an absolute path."""
    direct = Path(video)
    if direct.is_absolute() and direct.exists():
        return direct
    for p in (settings().root / "content").rglob("*"):
        if queue.is_video(p) and (p.name == video or p.stem == video):
            return p
    raise FileNotFoundError(f"{video} not found under content/")


def queue_status(days: int = 7) -> dict:
    s = settings()
    items = queue.scan(s.queue_dir)
    today = now().date()
    upcoming = queue.due(items, today - timedelta(days=30), today + timedelta(days=days))
    per_day: dict[str, int] = {}
    for i in upcoming:
        per_day[i.day.isoformat()] = per_day.get(i.day.isoformat(), 0) + 1
    return {"today": today.isoformat(), "post_time": s.post_time, "timezone": s.timezone, "mode": s.mode,
            "per_day": per_day, "videos": [i.summary() for i in upcoming],
            "loose_in_weeks": [i.summary() for i in items if i.day is None],
            "missing_copy": [i.video.name for i in upcoming if i.spec is None],
            "inbox": sorted(str(p) for p in s.inbox_dir.rglob("*") if queue.is_video(p)) if s.inbox_dir.exists() else []}


def check_video(video: str) -> dict:
    item, s = find(video), settings()
    p = media.probe(item.video)
    result = {"duration_s": round(p.duration_s, 2), "size": f"{p.width}x{p.height}", "size_mb": p.size_mb}
    for name in (item.spec and item.spec.platforms) or s.default_platforms:
        errors, warnings = media.check(p, name)
        result[name] = {"errors": errors, "warnings": warnings}
    return result


def write_post(video: str, caption: str, title: str = "", hashtags: list[str] | None = None,
               platforms_: list[str] | None = None, overrides: dict | None = None,
               publish_time: str | None = None, approved: bool = True, footer: bool = True,
               subtitles: str = "none", analysis_notes: dict | None = None) -> dict:
    item = find(video)
    spec = post.PostSpec.from_dict({"caption": caption, "title": title, "hashtags": hashtags or [],
                                    "platforms": platforms_ or [], "overrides": overrides or {},
                                    "publish_time": publish_time, "approved": approved, "footer": footer,
                                    "subtitles": subtitles, "analysis": analysis_notes or {}})
    path = queue.save_spec(item.video, spec)
    return {"saved": str(path), **preview_post(video)}


def preview_post(video: str) -> dict:
    item, s = find(video), settings()
    if item.spec is None:
        return {"error": item.spec_error or "no .post.yaml yet: write_post first"}
    out = {}
    for name in item.spec.platforms or s.default_platforms:
        c = post.render(item.spec, name, s.brand_footer)
        out[name] = {"title": c.title, "caption": c.caption, "chars": len(c.caption), "subtitles": c.subtitles,
                     "problems": post.validate(c), "backend": s.backend_for(name)}
    return {"video": item.video.name, "day": item.day and item.day.isoformat(), "copies": out}


def publish_due(dry_run: bool = True) -> list[dict]:
    return runner.run(settings(), now(), dry_run=dry_run)


def publish_now(video: str, dry_run: bool = True) -> list[dict]:
    """Publish one queued video right away, ignoring its slot time."""
    item = find(video)
    return runner.run(settings(), max(now(), runner.slot_for(item, 0, settings()) + timedelta(minutes=1)),
                      dry_run=dry_run, only=item.video.name)


def backends_status() -> dict:
    s = settings()
    out = {}
    for name in s.default_platforms:
        backend = s.backend_for(name)
        ok = name in SUPPORTED.get(backend, ())
        out[name] = {"backend": backend, "status": build(backend, name, s).check() if ok
                     else f"{backend} cannot publish {name}"}
    return out


def analyze_video(video: str, language: str = "es") -> dict:
    return analysis.analyze(locate(video), settings().analysis_dir, language)


def make_subtitles(video: str, burn: bool = False, language: str = "es") -> dict:
    """SRT next to the analysis; burn=True also renders a subtitled copy into content/library/."""
    src, s = locate(video), settings()
    segs = analysis.transcribe(src, language)
    if not segs:
        return {"video": str(src), "srt": None, "note": "no speech found"}
    srt = analysis.write_srt(segs, s.analysis_dir / src.stem / f"{src.stem}.srt")
    out = {"video": str(src), "srt": str(srt), "cues": srt.read_text(encoding="utf-8").count(" --> ")}
    if burn:
        out["burned"] = str(analysis.burn(src, srt, s.root / "content" / "library" / f"{src.stem}.subtitulado.mp4"))
        out["next"] = ("Review the burned file; if good, move the original to content/library/ and the subtitled "
                       "copy into the queue day folder with the original's name stem, then set subtitles: burned.")
    return out


def brand_info() -> dict:
    s = settings()
    return {"handles": s.brand_footer.handles, "footer_preview": {p: s.brand_footer.footer(p) for p in platforms.PLATFORMS},
            "missing": [p for p in platforms.PLATFORMS if p not in s.brand_footer.handles],
            "ask_user": "Before the first copy: confirm handles on every network, mentions/collabs, links and fixed hashtags."}


def platform_rules() -> str:
    return platforms.markdown_table()


def plan_week(week: str | None = None, apply: bool = False) -> dict:
    return planner.plan_week(settings(), now().date(), week, apply)


def mark_published(video: str, platform: str, url: str | None = None, status: str = "published") -> dict:
    return runner.mark_published(settings(), video, platform, url, status)


def pull_metrics() -> dict:
    return analytics.pull(settings())


def insights_report() -> dict:
    return analytics.report(settings())
