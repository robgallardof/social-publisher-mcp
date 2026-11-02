"""Durable proposals and owner-issued approvals. No credentials or generated code are stored."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict

from ..domain.code_mode import CodeModeError, CodeModeSettings
from ..domain.post import PostSpec, render, validate
from . import media, queue
from .locking import exclusive


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def asset_hash(path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def normalized(spec: PostSpec) -> dict:
    return {k: v for k, v in asdict(spec).items() if k not in ("approved", "code_mode_proposal")}


def policy(settings) -> dict:
    """Configuration hash includes provider target identities and privacy, never returns their values."""
    return {"timezone": settings.timezone, "post_time": settings.post_time,
            "stagger": settings.stagger_minutes, "mode": settings.mode, "brand": settings.brand,
            "catch_up": settings.catch_up, "ahead_days": settings.ahead_days,
            "max_attempts": settings.max_attempts,
            "backends": settings.backends, "accounts": settings.accounts,
            "code_mode": settings.code_mode, "platforms": settings.default_platforms}


def credential_binding(settings, targets) -> str:
    """Bind configured credentials without exposing them. Google access-token refresh is permitted.

    No live account directory exists. Conservatively invalidate approval on credential replacement;
    YouTube's stable refresh credential binds that identity while its short-lived access token rotates.
    """
    sources = {"youtube": "youtube_token", "tiktok": "tiktok", "instagram": "meta", "facebook": "meta"}
    identities = {}
    for platform in targets:
        path = settings.secrets_dir / (sources[platform] + ".json")
        if not path.exists():
            identities[platform] = None
        elif platform == "youtube":
            data = json.loads(path.read_text(encoding="utf-8"))
            identities[platform] = digest({"client_id": data.get("client_id"),
                                           "identity_credential": data.get("refresh_token") or data.get("token")})
        else:
            identities[platform] = asset_hash(path)
    return digest(identities)


def allowed(settings) -> list[str]:
    limits = CodeModeSettings.from_dict(settings.code_mode)
    return [p for p in settings.default_platforms if not limits.allowed_platforms or p in limits.allowed_platforms]


def find(settings, video: str) -> queue.Item:
    """Only unambiguous queue-relative names; reject traversal, absolute paths and escaping symlinks."""
    if not isinstance(video, str) or "\\" in video or not video or video.startswith("/"):
        raise CodeModeError("invalid_video")
    from pathlib import PurePosixPath
    if ".." in PurePosixPath(video).parts or ":" in video:
        raise CodeModeError("invalid_video")
    base = settings.queue_dir.resolve()
    matches = [i for i in queue.scan(settings.queue_dir)
               if i.video.relative_to(settings.queue_dir).as_posix() == video]
    if len(matches) != 1:
        raise CodeModeError("video_not_found")
    item = matches[0]
    for path in (item.video, item.sidecar, item.receipts_path):
        if not path.resolve().is_relative_to(base):
            raise CodeModeError("invalid_video")
    return item


def slot(settings, item):
    from .runner import slot_for
    same_day = sorted((i for i in queue.scan(settings.queue_dir) if i.day == item.day),
                      key=lambda i: i.video.name)
    index = next(n for n, i in enumerate(same_day) if i.video == item.video)
    return slot_for(item, index, settings)


def preview(settings, item, spec) -> dict:
    targets = spec.platforms or allowed(settings)
    if not targets or len(set(targets)) != len(targets) or not set(targets) <= set(allowed(settings)):
        raise CodeModeError("account_denied")
    info = media.probe(item.video)
    copies = {}
    for platform in targets:
        copy = render(spec, platform, settings.brand_footer)
        errors, warnings = media.check(info, platform)
        copies[platform] = {**asdict(copy), "problems": validate(copy) + errors, "warnings": warnings}
    return {"copies": copies, "media": asdict(info),
            "unverified": ["codec", "provider quota", "live OAuth scopes", "thumbnail", "file size limit"]}


class Approvals:
    def __init__(self, settings):
        self.settings = settings
        self.principal = CodeModeSettings.from_dict(settings.code_mode).principal
        self.path = settings.root / "content" / ".code-mode.sqlite"

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, principal TEXT NOT NULL, "
                   "snapshot TEXT NOT NULL, digest TEXT NOT NULL, status TEXT NOT NULL, expires REAL)")
        db.execute("CREATE TABLE IF NOT EXISTS audit (at REAL, execution TEXT, principal TEXT, "
                   "operation TEXT, status TEXT, duration_ms REAL)")
        try:
            with db:
                yield db
        finally:
            db.close()

    def audit(self, execution, operation, status, duration_ms=0):
        try:
            with self.connect() as db:
                db.execute("DELETE FROM audit WHERE at < ?", (time.time() - 30 * 86400,))
                db.execute("INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?)",
                           (time.time(), execution, self.principal, operation, status, duration_ms))
        except sqlite3.Error:
            raise CodeModeError("audit_unavailable") from None

    def propose(self, video: str, spec: PostSpec) -> dict:
        with exclusive(self.settings.root):
            item = find(self.settings, video)
            if item.day is None or item.receipts:
                raise CodeModeError("requires_unpublished_dated_video")
            spec.approved = False
            spec.code_mode_proposal = None
            spec.platforms = spec.platforms or allowed(self.settings)
            # Code Mode only schedules through official adapters; never routes to browser/handoff/Postiz.
            official = {"tiktok": "tiktok_api", "instagram": "meta_api", "facebook": "meta_api",
                        "youtube": "youtube_api"}
            if any(self.settings.backend_for(p) != official.get(p) for p in spec.platforms):
                raise CodeModeError("official_backend_required")
            view = preview(self.settings, item, spec)
            if any(c["problems"] for c in view["copies"].values()):
                return {"status": "VALIDATION_FAILED", **view}
            # Time overrides belong to the proposal, rather than the current sidecar.
            proposed_item = queue.Item(item.video, item.day, spec=spec)
            snapshot = {"video": video, "media_hash": asset_hash(item.video),
                        "previous_spec": asset_hash(item.sidecar) if item.sidecar.exists() else None,
                        "spec": normalized(spec), "policy_hash": digest(policy(self.settings)),
                        "at": slot(self.settings, proposed_item).isoformat(), "preview": view,
                        "credential_hash": credential_binding(self.settings, spec.platforms),
                        "targets": [{"platform": p, "alias": f"workspace:{p}", "configured_target":
                                     self.settings.accounts.get("meta", {}).get(
                                         "ig_user_id" if p == "instagram" else "page_id")
                                     if p in ("instagram", "facebook") else "credential-bound"}
                                    for p in spec.platforms],
                        "action": "schedule", "recurrence": None}
            pid, sha = uuid.uuid4().hex, digest(snapshot)
            with self.connect() as db:
                db.execute("INSERT INTO proposals VALUES (?, ?, ?, ?, 'PENDING_APPROVAL', NULL)",
                           (pid, self.principal, canonical(snapshot), sha))
            self.audit(pid, "posts.propose", "PENDING_APPROVAL")
            public = {k: v for k, v in snapshot.items() if k != "credential_hash"}
            return {"proposal_id": pid, "digest": sha, "status": "PENDING_APPROVAL", **public}

    def get(self, proposal_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM proposals WHERE id=? AND principal=?",
                             (proposal_id, self.principal)).fetchone()
        if row is None:
            raise CodeModeError("proposal_not_found")
        return {**dict(row), "snapshot": json.loads(row["snapshot"])}

    def approve(self, proposal_id: str, expected_digest: str, ttl_seconds: int = 604800) -> dict:
        """Trusted owner CLI only. Deliberately absent from the capability registry and MCP tools."""
        if not 1 <= ttl_seconds <= 30 * 86400:
            raise CodeModeError("invalid_approval_ttl")
        value = self.get(proposal_id)
        if value["digest"] != expected_digest or value["status"] != "PENDING_APPROVAL":
            raise CodeModeError("approval_mismatch")
        with self.connect() as db:
            result = db.execute("UPDATE proposals SET status='APPROVED', expires=? WHERE id=? "
                                "AND principal=? AND status='PENDING_APPROVAL' AND digest=?",
                                (time.time() + ttl_seconds, proposal_id, self.principal, expected_digest))
            if result.rowcount != 1:
                raise CodeModeError("approval_mismatch")
        self.audit(proposal_id, "owner.approve", "APPROVED")
        return self.get(proposal_id)

    def verify(self, value, item, activated=False):
        snapshot = value["snapshot"]
        if value["status"] not in ("APPROVED", "SCHEDULED") or (value["expires"] or 0) <= time.time():
            raise CodeModeError("approval_required_or_expired")
        if digest(snapshot) != value["digest"] or digest(policy(self.settings)) != snapshot["policy_hash"]:
            raise CodeModeError("approval_invalidated")
        if asset_hash(item.video) != snapshot["media_hash"]:
            raise CodeModeError("approval_invalidated")
        if credential_binding(self.settings, snapshot["spec"]["platforms"]) != snapshot["credential_hash"]:
            raise CodeModeError("approval_invalidated")
        if not set(snapshot["spec"]["platforms"]) <= set(allowed(self.settings)):
            raise CodeModeError("account_denied")
        if activated:
            if normalized(item.spec) != snapshot["spec"] or slot(self.settings, item).isoformat() != snapshot["at"]:
                raise CodeModeError("approval_invalidated")
        elif (asset_hash(item.sidecar) if item.sidecar.exists() else None) != snapshot["previous_spec"]:
            raise CodeModeError("approval_invalidated")

    def schedule(self, proposal_id: str) -> dict:
        with exclusive(self.settings.root):
            value = self.get(proposal_id)
            item = find(self.settings, value["snapshot"]["video"])
            # The sidecar is the durable activation record. Repairing a crash before the DB update is safe.
            activated = bool(item.spec and item.spec.code_mode_proposal == proposal_id)
            self.verify(value, item, activated)
            if not activated:
                if item.receipts:
                    raise CodeModeError("publication_already_started")
                spec = PostSpec(**value["snapshot"]["spec"], approved=True, code_mode_proposal=proposal_id)
                view = preview(self.settings, item, spec)
                if any(c["problems"] for c in view["copies"].values()):
                    raise CodeModeError("validation_failed")
                queue.save_spec(item.video, spec)
            with self.connect() as db:
                db.execute("UPDATE proposals SET status='SCHEDULED' WHERE id=?", (proposal_id,))
            self.audit(proposal_id, "schedule.create", "SCHEDULED")
            return {"proposal_id": proposal_id, "status": "SCHEDULED", "at": value["snapshot"]["at"]}

    def cancel(self, proposal_id: str) -> dict:
        with exclusive(self.settings.root):
            self.get(proposal_id)
            with self.connect() as db:
                db.execute("UPDATE proposals SET status='CANCELLED' WHERE id=? AND principal=?",
                           (proposal_id, self.principal))
            self.audit(proposal_id, "schedule.cancel", "CANCELLED")
            return {"proposal_id": proposal_id, "status": "CANCELLED",
                    "note": "Local future attempts cancelled; remote publications cannot be recalled."}

    def reconcile(self, proposal_id: str, platform: str, outcome: str, remote_id: str | None = None) -> dict:
        """Owner attests a remote outcome after checking the provider. Never available to generated code."""
        with exclusive(self.settings.root):
            value = self.get(proposal_id)
            item = find(self.settings, value["snapshot"]["video"])
            if platform not in value["snapshot"]["spec"]["platforms"]:
                raise CodeModeError("account_denied")
            previous = item.receipts.get(platform, {})
            if previous.get("status") not in ("unknown", "publishing"):
                raise CodeModeError("reconciliation_not_required")
            if outcome == "published" and remote_id:
                result = {"status": "published", "id": remote_id, "retry_eligible": False}
            elif outcome == "not_published" and remote_id is None:
                result = {"status": "failed", "retry_eligible": True, "error": "owner_verified_no_remote_effect"}
            else:
                raise CodeModeError("invalid_reconciliation")
            queue.record(item, platform, {**previous, **result}, increment=False)
            from .runner import complete
            if complete(item, self.settings):
                queue.archive(item, self.settings.published_dir)
            self.audit(proposal_id, f"owner.reconcile.{platform}", outcome)
            return {"proposal_id": proposal_id, "platform": platform, **result}


def guard(settings, item):
    if item.spec and item.spec.code_mode_proposal:
        approvals = Approvals(settings)
        value = approvals.get(item.spec.code_mode_proposal)
        approvals.verify(value, item, activated=True)
