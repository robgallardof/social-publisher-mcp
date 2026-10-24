"""The copy that goes with a video (`<video>.post.yaml`) and how it renders per platform. Pure."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import platforms

HASHTAG = re.compile(r"#[\wÀ-ɏ]+", re.UNICODE)
SUBTITLE_MODES = ("none", "burned", "auto", "srt")  # see skill `subtitles`


@dataclass(frozen=True)
class Copy:
    """What one platform receives."""
    platform: str
    caption: str                 # full text: body, brand footer, hashtags
    title: str | None = None     # YouTube only
    tags: tuple[str, ...] = ()   # YouTube keyword tags (not shown)
    privacy: str = "public"
    subtitles: str = "none"      # what the publisher must do about captions on this platform


@dataclass(frozen=True)
class Brand:
    """Cross-promotion added to every caption: the account's handles on the *other* networks."""
    handles: dict[str, str] = field(default_factory=dict)   # platform -> handle (without @ for social nets)
    footer_label: str = "📲 Síguenos también:"

    @classmethod
    def from_dict(cls, data: dict | None) -> "Brand":
        data = data or {}
        return cls({k: str(v).lstrip("@") for k, v in (data.get("handles") or {}).items() if v},
                   data.get("footer_label", cls.footer_label))

    def footer(self, platform: str) -> str:
        lines = []
        for key, handle in self.handles.items():
            if key == platform:
                continue
            name = platforms.PLATFORMS[key].name.split()[0] if key in platforms.PLATFORMS else key.title()
            lines.append(f"{name}: {handle}" if key == "facebook" else f"{name}: @{handle}")
        return f"{self.footer_label}\n" + "\n".join(lines) if lines else ""


@dataclass
class PostSpec:
    """Content of the sidecar YAML. Everything optional except one text field."""
    caption: str = ""
    title: str = ""
    hashtags: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)   # empty = config default
    overrides: dict[str, dict] = field(default_factory=dict)
    publish_time: str | None = None                      # "HH:MM", overrides the config post_time
    approved: bool = True
    footer: bool = True                                  # add the brand's other-network handles
    subtitles: str = "none"                              # none | burned | auto | srt
    analysis: dict = field(default_factory=dict)         # what analyze_video found (speech, summary...)

    @classmethod
    def from_dict(cls, data: dict | None) -> "PostSpec":
        data = data or {}
        unknown = set(data) - {f for f in cls.__dataclass_fields__}
        if unknown:
            raise ValueError(f"unknown keys in post file: {', '.join(sorted(unknown))}")
        spec = cls(**data)
        spec.hashtags = [normalize_tag(t) for t in spec.hashtags]
        for key in [*spec.platforms, *spec.overrides]:
            platforms.get(key)
        if spec.subtitles not in SUBTITLE_MODES:
            raise ValueError(f"subtitles must be one of {', '.join(SUBTITLE_MODES)}")
        return spec

    def to_dict(self) -> dict:
        out = {"title": self.title, "caption": self.caption, "hashtags": self.hashtags,
               "platforms": self.platforms, "overrides": self.overrides,
               "publish_time": self.publish_time, "approved": self.approved,
               "footer": self.footer, "subtitles": self.subtitles, "analysis": self.analysis}
        return {k: v for k, v in out.items()
                if v not in ("", [], {}, None) and not (k == "footer" and v) and not (k == "subtitles" and v == "none")}


def normalize_tag(tag: str) -> str:
    tag = tag.strip().replace(" ", "")
    return tag if tag.startswith("#") else f"#{tag}"


def _join(text: str, footer: str, tags: list[str]) -> str:
    missing = [t for t in tags if t.lower() not in text.lower()]
    parts = [text.rstrip(), footer, " ".join(missing)]
    return "\n\n".join(p for p in parts if p).strip()


def render(spec: PostSpec, platform: str, brand: Brand | None = None) -> Copy:
    """Apply overrides and assemble the final text for one platform: body, footer, hashtags."""
    p = platforms.get(platform)
    o = spec.overrides.get(platform, {})
    tags = [normalize_tag(t) for t in o.get("hashtags", spec.hashtags)]
    text = o.get("caption", spec.caption)
    title = o.get("title", spec.title) or None
    if p.title_max is None and title and title not in text:
        text = f"{title}\n\n{text}".strip() if text else title
        title = None
    footer = brand.footer(platform) if brand and o.get("footer", spec.footer) else ""
    yt_tags = tuple(o.get("tags", [t.lstrip("#") for t in tags]))
    return Copy(platform, _join(text, footer, tags), title, yt_tags, o.get("privacy", "public"),
                o.get("subtitles", spec.subtitles))


def validate(copy: Copy) -> list[str]:
    """Blocking problems for one rendered copy (empty list = ready)."""
    p = platforms.get(copy.platform)
    errors = []
    if not copy.caption and not copy.title:
        errors.append("empty text")
    if len(copy.caption) > p.caption_max:
        errors.append(f"caption {len(copy.caption)} chars > {p.caption_max}")
    if p.title_max is not None:
        if not copy.title:
            errors.append("missing title")
        elif len(copy.title) > p.title_max:
            errors.append(f"title {len(copy.title)} chars > {p.title_max}")
        if any(c in (copy.title or "") for c in "<>"):
            errors.append("title cannot contain < or >")
    n_tags = len(HASHTAG.findall(copy.caption))
    if n_tags > p.hashtags_max:
        errors.append(f"{n_tags} hashtags > {p.hashtags_max}")
    if copy.platform == "youtube" and sum(len(t) + 1 for t in copy.tags) > 500:
        errors.append("YouTube tags exceed 500 characters")
    return errors
