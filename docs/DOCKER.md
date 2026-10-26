# Docker (optional)

Everything works natively with `uv`; Docker is for people who prefer not to install Python. The image only holds the
`social-forge` code. Your videos, `config/social.yaml`, `secrets/` and analytics stay in this folder and are mounted at
`/workspace` when the container runs — they are never copied into the image (`.dockerignore` is an allowlist).

```bash
docker build -t social-forge:local .                                    # MCP + CLI, YouTube API backend
docker build --build-arg EXTRAS=youtube,analysis -t social-forge:local . # + faster-whisper transcripts
```

| Backend | In Docker |
|---|---|
| `youtube_api`, `meta_api`, `tiktok_api`, `postiz` | Yes (credentials from the mounted `secrets/` and `config/`) |
| `handoff` | Yes (writes tasks to `content/handoff/` for an agent on the host) |
| `browser` (Playwright profile) | **No.** Its one-time login needs a desktop browser; run it natively |

Video probing uses the ffmpeg bundled with `imageio-ffmpeg`, so no system ffmpeg is needed.

## stdio: launched by your MCP client

No port and no token. Keep `-i` and never add `-t` (a TTY corrupts JSON-RPC):

```json
{
  "mcpServers": {
    "social-forge": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-v", "C:/path/to/social-publisher-mcp:/workspace", "social-forge:local"]
    }
  }
}
```

## HTTP with a token

```bash
export SOCIAL_FORGE_MCP_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SOCIAL_FORGE_PORT=8766          # optional, default 8080
docker compose up -d --build --wait social-forge
```

```powershell
$env:SOCIAL_FORGE_MCP_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
$env:SOCIAL_FORGE_PORT = '8766'
docker compose up -d --build --wait social-forge
```

Point a Streamable HTTP MCP client at `http://127.0.0.1:<port>/mcp` with `Authorization: Bearer <token>`.

| Variable | Default | Purpose |
|---|---|---|
| `SOCIAL_FORGE_MCP_TOKEN` | required | Bearer token, at least 32 characters |
| `SOCIAL_FORGE_PORT` | `8080` | Host port (container port is always 8080) |
| `SOCIAL_FORGE_BIND_ADDRESS` | `127.0.0.1` | Interface Docker publishes on; loopback only by default |
| `SOCIAL_FORGE_WORKSPACE` | `.` | Folder mounted at `/workspace` |
| `SOCIAL_FORGE_USER` | `10001:10001` | Runtime UID:GID; on Linux use `"$(id -u):$(id -g)"` |
| `SOCIAL_FORGE_EXTRAS` | `youtube` | Build extras for `docker compose build` |

Native equivalent: `uv run social-forge-mcp --http --listen 127.0.0.1:8766`. `/healthz` answers without a token;
requests with an `Origin` header (browsers) and unknown `Host` names are rejected. It is a single-user service:
put a TLS reverse proxy in front before exposing it beyond your machine and allow its name with `--allow-host`.

## CLI and the 05:00 publishing

```bash
docker compose run --rm cli status
docker compose run --rm cli run-due --dry-run
```

The container does not schedule anything by itself. Point your host scheduler at the one-shot CLI instead of the
native command, e.g. cron `0 5 * * * cd /path/to/social-publisher-mcp && docker compose run --rm cli run-due`, or
a Windows Task Scheduler action running the same command. Receipts in the queue prevent double posting on retries.

## Verify

```bash
python scripts/test_docker.py                          # default image
python scripts/test_docker.py --extras youtube,analysis
```

Builds the image, checks it contains no personal data, speaks MCP over stdio, runs the CLI service and the HTTP
service with a token on a free port, and calls a real tool. It uses a temporary workspace, never your content.

### Verification — 2026-10-26

Executed on Windows with Docker Desktop Linux containers: default `EXTRAS=youtube`
image build, personal-data exclusion check, real stdio tool call, Compose CLI status,
and authenticated HTTP with 15 tools on a custom port. All passed. Native suite:
`uv run pytest -q` — 53 passed. No live publishing or user credentials were used.
The optional `analysis` image and real platform API publishing were NOT EXECUTED
in this verification. README quickstart now generates a real token rather than
using shell redirection placeholders.
