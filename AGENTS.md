# social-publisher-mcp — instructions for any agent

AI community manager for short-form video: **TikTok, Instagram Reels, Facebook Reels and YouTube Shorts**.
It keeps a dated queue of finished videos, writes the copy for each platform, publishes everything of a day at
**05:00** (America/Mexico_City by default) and analyses the audience. Works with any agent that supports `AGENTS.md`,
Agent Skills (`SKILL.md`) and MCP: Claude Code, Codex, Cursor, Gemini CLI, Antigravity, VS Code.
Skills and roles are written in English; always reply to the user in the user's language.

**Current brand: Chomi la ardilla** (Facebook page "Chomi la ardilla", Instagram @chomiescuincla, TikTok
@andrearuizdmn). Brand data lives only in `brand/` and `config/social.yaml` → `brand`, so the same setup serves
any other account. Before the first copy for a brand, ASK the user for handles on every network, @mentions,
links, fixed hashtags and subtitle preference (`community-manager` → "Ask first"); don't wait for them to say it.

## Install as an MCP (any client)

`social-forge` is a stdio MCP server. It exposes the tools, plus every skill as a resource (`skill://<name>`) and
every role as a prompt, so a client that only speaks MCP still gets the playbooks.
- Inside this folder: `python scripts/sync.py` writes `.mcp.json` (Claude Code), `.codex/config.toml`,
  `.cursor/mcp.json`, `.gemini/settings.json`, `.vscode/mcp.json` and `.agents/mcp_config.json` (Antigravity).
- For your user, from any folder: `python scripts/install-mcp.py` (Claude Code, Claude Desktop, Codex, Gemini CLI,
  Antigravity, Cursor, VS Code, Windsurf — whichever are installed; `--list`, `--dry-run`, `--remove`,
  `--with-skills` also links skills/roles into `~/.claude`). It sets `SOCIAL_FORGE_ROOT` to this folder.

## What is here

| Path | What it is |
|---|---|
| `content/inbox/` | Where the user drops new videos (never the repo root); the agent analyses and moves them |
| `content/library/` | Raw/full takes and rendered versions (e.g. burned subtitles) not in the queue |
| `content/queue/` | Finished videos in `YYYY-MM-DD/` (or `YYYY-Www/`) folders + their `.post.yaml` copy |
| `content/published/`, `content/handoff/` | Archive with receipts; tasks for agent/manual uploads |
| `brand/` | Voice, audience, hashtag bank — read before writing copy |
| `analytics/` | `metrics.csv` snapshots, weekly reports, research notes, audience notes; `videos/<stem>/` frames, transcript, .srt |
| `mcp/social-forge/` | Our MCP + CLI: queue, copy, publishers (APIs, Postiz, browser, handoff), runner, metrics. Python 3.12 + uv |
| `config/social.yaml` | Time, timezone, mode, backend per platform, account ids (copy of `social.example.yaml`) |
| `config/browser_flows.yaml` | Selectors for the browser backend (data, editable) |
| `config/mcp.servers.json` | Single source of MCP servers → `python scripts/sync.py` generates each client's config |
| `secrets/` | Credentials (git-ignored). Never print or copy their contents |
| `docs/accounts.md` | How to get each platform's credentials |

## How to work

1. Pick the role (if your runtime has no subagents, read the file and follow it yourself):
   - anything general, daily/weekly routines → `.agents/agents/community-manager.md` (the lead)
   - what a video is about, transcript, subtitles → `video-analyst`
   - planning, how many per day, week folders → `content-strategist`
   - titles, captions, hashtags → `copywriter`
   - uploading, failures, logins → `publisher`
   - metrics, audience, reports → `audience-analyst`
   - trends, competitors, platform rule checks → `trend-researcher`
2. Skills (`.agents/skills/`):
   | Skill | Use it for |
   |---|---|
   | `content-queue` | Folder convention, inbox, `.post.yaml`, receipts, the 05:00 rule |
   | `video-analysis` | Frames + transcript before writing; summary saved in the post |
   | `subtitles` | none / auto / burned / srt and how each platform turns captions on |
   | `platform-copywriting` | Per-platform copy, limits (`references/platforms.md`), formulas |
   | `social-publishing` | Backends, modes, scheduled task, failures; `references/<platform>.md` playbooks |
   | `agent-browser-upload` | Uploading / reading insights by driving Chrome, Playwright MCP or computer use |
   | `content-strategy` | Pillars, cadence, sequencing, experiments |
   | `audience-analytics` | KPIs, metrics, weekly report |
   | `trend-research` | Trends, competitors, verifying platform claims |
   | `community-engagement` | Comments, moderation, DMs triage |
3. Always `dry_run=true` first. Real publishing only from the scheduled task or with the user's explicit OK.
4. Safety: never delete videos; never double-post (check receipts); never type passwords/2FA; credentials only in `secrets/`.

## Developing social-forge

- Layers: `domain/` (pure rules: platforms, post copy + brand footer, subtitles/SRT, schedule, insights) → `services/` (queue on disk, media probe,
  runner, planner, analytics, analysis (frames/transcript/burn), `publishers/`) → `app.py` (use cases) → thin `server.py` (MCP) and `cli.py`.
- New backend: a class with `name`, `native_schedule`, `publish(job, now) -> receipt`, `check()` in `services/publishers/`,
  registered in `publishers/__init__.py` (`build` + `SUPPORTED`). Add a MockTransport test.
- Platform limits live only in `domain/platforms.py`; `platform-copywriting/references/platforms.md` is generated.
- Tests: `cd mcp/social-forge && uv run pytest` (no network: HTTP shapes via httpx.MockTransport, real ffmpeg probe).
- After editing `config/` or `.agents/`, run `python scripts/sync.py`.
- Docker (optional): `Dockerfile` + `compose.yaml` (stdio, or HTTP with `SOCIAL_FORGE_MCP_TOKEN`; `cli` service for
  `run-due`). The image never contains personal data (`.dockerignore` allowlist). Real test: `python scripts/test_docker.py`.
- Commits: run `git config core.hooksPath .githooks` once per clone; the `commit-msg` hook strips AI co-author trailers.
