#!/bin/sh
# One-time setup on macOS / Linux. Schedule with cron instead of install-schedule.ps1:
#   0 5,6,7 * * *  cd <repo>/mcp/social-forge && uv run --no-sync social-forge run-due >> ../../logs/cron.log 2>&1
set -e
command -v deno >/dev/null 2>&1 || {
    echo "Deno 2 is required for Code Mode. Install it from https://docs.deno.com/runtime/getting_started/installation/ and rerun setup." >&2
    exit 1
}
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root/mcp/social-forge"
uv sync --python 3.12 --extra youtube --extra browser --extra analysis
uv run playwright install chromium
uv run pytest -q
[ -f "$root/config/social.yaml" ] || cp "$root/config/social.example.yaml" "$root/config/social.yaml"
mkdir -p "$root/secrets"
python3 "$root/scripts/sync.py"
python3 "$root/scripts/install-mcp.py"
echo "Next: docs/accounts.md (credentials), then add the cron line above"
