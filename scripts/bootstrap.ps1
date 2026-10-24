# One-time setup on Windows: Python env with every backend, Playwright browser, agent configs.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $root "mcp\social-forge")
try {
    uv sync --python 3.12 --extra youtube --extra browser --extra analysis
    uv run playwright install chromium
    uv run pytest -q
} finally { Pop-Location }
$cfg = Join-Path $root "config\social.yaml"
if (-not (Test-Path $cfg)) { Copy-Item (Join-Path $root "config\social.example.yaml") $cfg; Write-Host "Creado config\social.yaml" }
New-Item -ItemType Directory -Force (Join-Path $root "secrets") | Out-Null
python (Join-Path $root "scripts\sync.py")
python (Join-Path $root "scripts\install-mcp.py")   # user-level MCP in Claude Code, Codex, Antigravity, Cursor, VS Code...
Write-Host "`nSiguiente: docs\accounts.md (credenciales), luego scripts\install-schedule.ps1"
