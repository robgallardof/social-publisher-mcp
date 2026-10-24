"""Per-platform publishing rules. Pure data: the single source of truth for limits and specs.

Values come from the official developer docs (checked 2026-10). Re-check them with the
`trend-research` skill when a platform changes; `references/platforms.md` is generated from here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Platform:
    key: str
    name: str
    min_duration_s: float
    max_duration_s: float
    caption_max: int            # characters in the main text field
    title_max: int | None       # None = the platform has no separate title
    hashtags_max: int           # hard cap or sensible cap
    hashtags_recommended: str
    aspect: str                 # recommended aspect ratio
    resolution: str
    api_daily_limit: int | None # posts per rolling 24 h through the API
    native_schedule: str        # how the official API schedules (or "none")
    notes: str


PLATFORMS: dict[str, Platform] = {p.key: p for p in (
    Platform("tiktok", "TikTok", 3, 600, 2200, None, 5, "3-5 niche + 1 broad",
             "9:16", "1080x1920", None, "none (post at the time; TikTok Studio web can schedule up to 10 days)",
             "Unaudited API clients can only post SELF_ONLY (private). Saves, shares and completion rate rank."),
    Platform("instagram", "Instagram Reels", 3, 900, 2200, None, 30, "3-5 specific (more looks spammy)",
             "9:16", "1080x1920", 50, "none (Graph API has no publish time: post at the time)",
             "Business account (Instagram Login API). Cover frame and first line of caption matter; keywords > hashtags."),
    Platform("facebook", "Facebook Reels", 3, 90, 2200, None, 5, "0-3",
             "9:16", "1080x1920", 30, "video_state=SCHEDULED + scheduled_publish_time (10 min to 29 days ahead)",
             "Page Reels via /{page-id}/video_reels. Longer than 90 s is published as a regular video."),
    Platform("youtube", "YouTube Shorts", 1, 180, 5000, 100, 15, "2-3 (#shorts optional)",
             "9:16", "1080x1920", None, "status.privacyStatus=private + status.publishAt (ISO 8601)",
             "Unverified Google Cloud projects upload as private only until the API audit. Title = search keywords."),
)}

VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".webm")


def get(key: str) -> Platform:
    try:
        return PLATFORMS[key]
    except KeyError:
        raise ValueError(f"unknown platform {key!r}; use one of {', '.join(PLATFORMS)}") from None


def markdown_table() -> str:
    head = ("| Platform | Duration | Caption | Title | Hashtags | Aspect | API limit/24 h | Native schedule |\n"
            "|---|---|---|---|---|---|---|---|\n")
    rows = "".join(
        f"| {p.name} | {p.min_duration_s:g}-{p.max_duration_s:g} s | {p.caption_max} | {p.title_max or '-'} | "
        f"max {p.hashtags_max} ({p.hashtags_recommended}) | {p.aspect} {p.resolution} | {p.api_daily_limit or '-'} | "
        f"{p.native_schedule} |\n" for p in PLATFORMS.values())
    notes = "".join(f"- **{p.name}**: {p.notes}\n" for p in PLATFORMS.values())
    return head + rows + "\n" + notes
