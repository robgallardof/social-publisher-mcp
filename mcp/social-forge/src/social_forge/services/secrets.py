"""Credentials live in <root>/secrets/*.json (git-ignored). Never log or return their values."""

from __future__ import annotations

import json
from pathlib import Path

from ..config import Settings


class MissingSecret(RuntimeError):
    pass


def path(settings: Settings, name: str) -> Path:
    return settings.secrets_dir / f"{name}.json"


def load(settings: Settings, name: str, *keys: str) -> dict:
    p = path(settings, name)
    if not p.exists():
        raise MissingSecret(f"missing secrets/{name}.json (see docs/accounts.md)")
    data = json.loads(p.read_text(encoding="utf-8"))
    missing = [k for k in keys if not data.get(k)]
    if missing:
        raise MissingSecret(f"secrets/{name}.json lacks {', '.join(missing)} (see docs/accounts.md)")
    return data


def save(settings: Settings, name: str, data: dict) -> Path:
    settings.secrets_dir.mkdir(parents=True, exist_ok=True)
    p = path(settings, name)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p
