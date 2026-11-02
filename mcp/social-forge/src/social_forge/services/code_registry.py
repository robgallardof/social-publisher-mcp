"""Small explicit allowlist over existing domain/services, with schemas derived from Python types."""

from __future__ import annotations

import inspect
import time
from dataclasses import asdict, dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

from ..domain import platforms, post
from ..domain.code_mode import CodeModeError
from . import analytics, media, queue
from .code_approvals import Approvals, allowed, find, preview

Platform = Literal["tiktok", "instagram", "facebook", "youtube"]


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    caption: str = Field(max_length=10000)
    title: str = Field(default="", max_length=200)
    hashtags: list[str] = Field(default_factory=list, max_length=30)
    platforms: list[Platform] = Field(min_length=1, max_length=4)
    # Privacy overrides are validated here rather than accepting arbitrary provider payloads.
    privacy: Literal["public", "private", "unlisted"] = "public"
    subtitles: Literal["none", "burned"] = "none"

    def spec(self):
        return post.PostSpec.from_dict({"caption": self.caption, "title": self.title,
                                       "hashtags": self.hashtags, "platforms": self.platforms,
                                       "subtitles": self.subtitles, "approved": False,
                                       "overrides": {p: {"privacy": self.privacy} for p in self.platforms}})


@dataclass
class Capability:
    name: str
    handler: object
    description: str
    permission: str
    effect: str = "read"
    approval: bool = False

    def __post_init__(self):
        from typing import get_type_hints
        hints = get_type_hints(self.handler)
        params = inspect.signature(self.handler).parameters
        self.model = create_model(self.name.replace(".", "_"), __config__=ConfigDict(extra="forbid", strict=True),
                                  **{n: (hints[n], ... if p.default is inspect.Parameter.empty else p.default)
                                     for n, p in params.items()})

    def describe(self, providers):
        schema = self.model.model_json_schema()
        fields = ", ".join(f"{k}{'' if k in schema.get('required', []) else '?'}: "
                           f"{v.get('type', 'object')}" for k, v in schema.get("properties", {}).items())
        return {"name": self.name, "description": self.description, "input_schema": schema,
                "output_schema": {"type": "object"}, "permissions": [self.permission],
                "providers": providers, "content_types": ["short_video"], "side_effect": self.effect,
                "requires_approval": self.approval, "version": "1", "availability": "implemented",
                "limitations": "Single workspace owner; configured accounts only; provider capabilities differ.",
                "signature": f"social.{self.name}({{{fields}}}): Promise<object>"}


class Registry:
    def __init__(self, settings, execution_id="direct"):
        self.settings, self.execution_id = settings, execution_id
        self.approvals = Approvals(settings)
        self.providers = allowed(settings)
        # No dynamic getattr dispatch: direct publishing, OAuth, generic paths and owner approval are absent.
        definitions = [
            Capability("accounts.list", self.accounts, "List configured account aliases, not live OAuth status", "accounts:read"),
            Capability("accounts.capabilities", self.requirements, "Provider publishing requirements and restrictions", "accounts:read"),
            Capability("queue.list", self.queue, "List dated queue video identifiers", "content:read"),
            Capability("media.inspect", self.inspect, "Validate duration resolution aspect ratio for selected platforms", "content:read"),
            Capability("posts.preview", self.preview, "Prepare draft captions and validate copies without saving to queue", "content:read"),
            Capability("posts.propose", self.propose, "Persist exact media content privacy accounts and schedule for owner approval", "proposals:write", "local_write"),
            Capability("posts.status", self.status, "Read proposal approval and per-provider receipt states", "proposals:read"),
            Capability("schedule.create", self.schedule, "Activate an owner-approved schedule in the existing durable queue", "schedule:write", "local_write", True),
            Capability("schedule.cancel", self.cancel, "Cancel local future attempts; cannot delete remote posts", "schedule:write", "local_write"),
            Capability("analytics.summary", self.summary, "Combine cached local metrics; no new API requests", "analytics:read"),
        ]
        self.capabilities = {c.name: c for c in definitions}

    def search(self, query: str = "", provider: Platform | None = None, read_only: bool = False,
               limit: int = 5) -> dict:
        if not isinstance(query, str) or len(query) > 512 or type(limit) is not int or not 1 <= limit <= 10:
            raise CodeModeError("invalid_search")
        if provider and provider not in self.providers:
            raise CodeModeError("account_denied")
        words = query.lower().split()
        scored = []
        for c in self.capabilities.values():
            description = c.describe(self.providers)
            if read_only and c.effect != "read":
                continue
            haystack = str(description).lower()
            score = sum(3 if word in c.name.lower() else 1 for word in words if word in haystack)
            if not words or score:
                scored.append((score, c.name, description))
        scored.sort(key=lambda row: (-row[0], row[1]))
        return {"capabilities": [v for _, _, v in scored[:limit]], "matches": len(scored)}

    def dispatch(self, name, arguments, *, permissions=None):
        started = time.perf_counter()
        status = "denied"
        c = self.capabilities.get(name) if isinstance(name, str) else None
        try:
            if c is None or (permissions is not None and c.permission not in permissions):
                raise CodeModeError("capability_denied")
            if not isinstance(arguments, dict):
                raise CodeModeError("invalid_arguments")
            parsed = c.model.model_validate(arguments)
            result = c.handler(**{key: getattr(parsed, key) for key in c.model.model_fields})
            status = "ok"
            return result
        except ValidationError:
            raise CodeModeError("invalid_arguments") from None
        except CodeModeError:
            raise
        except Exception:  # noqa: BLE001 - boundary must not expose trusted-service exception content
            # Provider exceptions may contain authorization headers, URLs and private filesystem paths.
            raise CodeModeError("operation_failed") from None
        finally:
            self.approvals.audit(self.execution_id, c.name if c else "unknown", status,
                                 (time.perf_counter() - started) * 1000)

    def accounts(self) -> dict:
        return {"accounts": [{"id": f"workspace:{p}", "platform": p,
                              "backend": self.settings.backend_for(p), "authentication": "not_checked"}
                             for p in self.providers], "scope": "single-workspace"}

    def requirements(self, platform: Platform) -> dict:
        if platform not in self.providers:
            raise CodeModeError("account_denied")
        from .publishers import SUPPORTED
        backend = self.settings.backend_for(platform)
        return {"account_id": f"workspace:{platform}", "backend": backend,
                "supported": platform in SUPPORTED.get(backend, ()),
                "rules": asdict(platforms.get(platform)), "source": "repository domain/platforms.py",
                "live_permissions": "not_checked", "code_mode_scheduling": backend in
                ("meta_api", "youtube_api", "tiktok_api"),
                "unsupported": ["delete", "recurrence", "arbitrary accounts", "live quota negotiation"]}

    def queue(self, days: int = 7) -> dict:
        if not 1 <= days <= 30:
            raise CodeModeError("invalid_arguments")
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo(self.settings.timezone)).date()
        videos = []
        for item in queue.scan(self.settings.queue_dir):
            if item.day and today - timedelta(days=30) <= item.day <= today + timedelta(days=days):
                video = item.video.relative_to(self.settings.queue_dir).as_posix()
                find(self.settings, video)
                videos.append({"video": video, "day": str(item.day), "has_copy": bool(item.spec),
                               "receipts": {p: r.get("status") for p, r in item.receipts.items() if p in self.providers}})
                if len(videos) >= 200:
                    break
        return {"videos": videos, "limit": 200, "timezone": self.settings.timezone, "post_time": self.settings.post_time}

    def inspect(self, video: str, targets: list[Platform]) -> dict:
        if not targets or not set(targets) <= set(self.providers):
            raise CodeModeError("account_denied")
        item = find(self.settings, video)
        probe = media.probe(item.video)
        checks = {}
        for target in targets:
            errors, warnings = media.check(probe, target)
            checks[target] = {"errors": errors, "warnings": warnings}
        return {"media": asdict(probe), "platforms": checks,
                "unverified": ["codec", "live provider restrictions", "file size limit"]}

    def preview(self, video: str, draft: Draft) -> dict:
        return preview(self.settings, find(self.settings, video), draft.spec())

    def propose(self, video: str, draft: Draft) -> dict:
        # Existing TikTok adapter controls privacy through account settings, not PostSpec.
        # Do not promise an approved privacy setting which that adapter cannot honor.
        if any(p != "youtube" for p in draft.platforms) and draft.privacy != "public":
            raise CodeModeError("privacy_unsupported")
        if "tiktok" in draft.platforms and self.settings.accounts.get("tiktok", {}).get(
                "privacy_level", "PUBLIC_TO_EVERYONE") != "PUBLIC_TO_EVERYONE":
            raise CodeModeError("privacy_unsupported")
        return self.approvals.propose(video, draft.spec())

    def status(self, proposal_id: str) -> dict:
        value = self.approvals.get(proposal_id)
        video = value["snapshot"]["video"]
        try:
            item = find(self.settings, video)
        except CodeModeError:
            # Archived receipts remain queryable without accepting user-supplied filesystem paths.
            from pathlib import Path
            path = self.settings.published_dir / Path(video).name
            matches = list(self.settings.published_dir.rglob(path.name))
            matches = [p for p in matches if p.resolve().is_relative_to(self.settings.published_dir.resolve())]
            item = queue.load_item(matches[0], None) if len(matches) == 1 else None
        receipts = {p: {k: v for k, v in r.items() if k in ("status", "id", "attempts", "operation_id", "retry_eligible")}
                    for p, r in (item.receipts if item else {}).items() if p in self.providers}
        states = {r.get("status") for r in receipts.values()}
        state = value["status"]
        if states and states <= {"published", "scheduled"} and len(receipts) == len(value["snapshot"]["spec"]["platforms"]):
            state = "PUBLISHED" if states == {"published"} else "SCHEDULED"
        elif "published" in states or "scheduled" in states:
            state = "PARTIALLY_PUBLISHED"
        elif "unknown" in states or "publishing" in states:
            state = "UNKNOWN"
        elif "failed" in states:
            state = "FAILED"
        return {"proposal_id": proposal_id, "status": state, "approval_status": value["status"],
                "digest": value["digest"], "expires": value["expires"], "receipts": receipts,
                "next_action": "Reconcile UNKNOWN manually; retry only explicitly safe failures."}

    def schedule(self, proposal_id: str) -> dict:
        return self.approvals.schedule(proposal_id)

    def cancel(self, proposal_id: str) -> dict:
        return self.approvals.cancel(proposal_id)

    def summary(self) -> dict:
        from ..domain.insights import summarize
        metrics = [m for m in analytics.read(self.settings.metrics_csv) if m.platform in self.providers]
        return {"summary": summarize(metrics), "source": "analytics/metrics.csv", "freshness": "cached",
                "collected_at": self.settings.metrics_csv.stat().st_mtime if self.settings.metrics_csv.exists() else None,
                "limitations": "Legacy CSV stores unavailable fields as zero; do not infer availability from zero.",
                "unavailable": ["watch time", "reach", "impressions", "account demographics"]}
