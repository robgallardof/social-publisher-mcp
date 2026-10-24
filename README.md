<div align="center">

# 📲 social-publisher-mcp

**An AI community manager for short-form video, packaged as an MCP server.**<br>
Drop your finished videos in a folder. It watches them, writes the copy for every network,<br>
schedules everything for **05:00**, adds subtitles when they're needed and tells you what worked.

[![tests](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio-8A2BE2)
![platforms](https://img.shields.io/badge/TikTok%20·%20Reels%20·%20Facebook%20·%20Shorts-ff3b5c)
![OS](https://img.shields.io/badge/Windows%20·%20macOS%20·%20Linux-555)

**English** · [Español](README.es.md)

</div>

---

## ✨ What it does

| | |
|---|---|
| 📂 **Dated queue** | `content/queue/2026-10-27/*.mp4` goes out on Oct 27. Three videos in the folder = three posts at 05:00. Week folders (`2026-W44/`) are spread over the days for you. |
| 👀 **Watches every video** | 8-frame contact sheet + Spanish/any-language transcript (faster-whisper) → it knows what happens, whether there is speech and whether subtitles are already burned in. |
| ✍️ **Per-platform copy** | Hook, body, CTA, hashtags and keywords tuned for TikTok, Instagram Reels, Facebook Reels and YouTube Shorts, validated against each platform's real limits. |
| 🔁 **Cross-promotion footer** | Every caption ends with `📲 Follow us too:` and your handles on the *other* networks — automatically. |
| 💬 **Subtitles** | Decides none / platform auto-captions / `.srt` / burned-in, and renders burned subtitles styled for vertical video. |
| 🚀 **Publishes any way it can** | Official APIs (Meta, YouTube, TikTok) → Postiz → a Playwright browser profile → handing the task to the agent itself (Claude in Chrome, Playwright MCP, computer use). |
| ⏰ **05:00 every day** | A Windows scheduled task (cron on macOS/Linux) runs the idempotent publisher with retries, wakes the PC and catches up if it was off. |
| 📈 **Learns** | Pulls metrics, finds the best weekdays and top/bottom videos, and writes a weekly report with at most three actions. |

## 🧩 Works with every agent

`social-forge` is a standard **stdio MCP server**. Besides its tools it exposes every **skill as an MCP resource** (`skill://<name>`) and every **role as an MCP prompt**, so any MCP client gets the full playbook — not just the ones that read `.agents/`.

| Client | How |
|---|---|
| Claude Code | `.mcp.json` in the folder, or user-wide via the installer (+ skills/agents linked into `~/.claude`) |
| Codex | `.codex/config.toml` / `~/.codex/config.toml` |
| Antigravity | `.agents/mcp_config.json` / `~/.gemini/antigravity/mcp_config.json` |
| Cursor · VS Code · Gemini CLI · Windsurf · Claude Desktop | generated config files, or the installer |

```powershell
python scripts/install-mcp.py --list         # which clients are installed
python scripts/install-mcp.py --with-skills  # register for your user everywhere (backs up each file as .bak)
python scripts/install-mcp.py --remove       # undo
python scripts/install-mcp.py --workspace ../davinci-agents  # any other workspace with config/mcp.servers.json
```

## 🚀 Quick start

```powershell
git clone https://github.com/robgallardof/social-publisher-mcp.git
cd social-publisher-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1        # env, tests, configs, MCP
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 # daily 05:00 task
```

macOS / Linux: `sh scripts/bootstrap.sh` and the cron line printed at the end. Requires [uv](https://docs.astral.sh/uv/).

Then talk to your agent:

> *"Process the inbox"* · *"Prepare tomorrow"* · *"Spread week 44, two per day"* · *"Add subtitles to the storytime"* · *"What worked this week?"* · *"Find squirrel trends in Mexico"*

## 🔄 How a video flows

```mermaid
flowchart LR
    A[content/inbox] -->|analyze_video| B(frames + transcript)
    B --> C{video-analyst}
    C -->|day folder| D[content/queue/YYYY-MM-DD]
    D -->|write_post| E[.post.yaml<br/>copy · footer · subtitles]
    E -->|05:00 run-due| F{backend}
    F --> G[Meta / YouTube / TikTok API]
    F --> H[Postiz]
    F --> I[Browser profile]
    F --> J[Agent handoff]
    G & H & I & J --> K[content/published + receipts]
    K -->|pull_metrics| L[analytics · weekly report]
```

## 🛠️ MCP tools (15)

| Tool | |
|---|---|
| `queue_status` | What goes out each day, overdue, missing copy, new videos in the inbox |
| `plan_week` | Spread a week folder over its remaining days |
| `analyze_video` | Frames, transcript, speech yes/no, `.srt` |
| `make_subtitles` | `.srt`, optionally a burned-in copy for review |
| `check_video` | Duration/resolution vs each platform |
| `write_post` · `preview_post` | Save and preview the per-platform copy (footer added automatically) |
| `brand_info` | Handles per network and what's missing |
| `publish_due` · `publish_now` | Publish or pre-schedule (always `dry_run` first) |
| `mark_published` | Close an agent/manual upload |
| `backends_status` | Is every platform ready? |
| `platform_rules` | Limits per platform |
| `pull_metrics` · `insights_report` | Metrics snapshot and summary |

## 👥 Roles and skills

**Roles** (`.agents/agents/`): `community-manager` (lead) · `video-analyst` · `content-strategist` · `copywriter` · `publisher` · `audience-analyst` · `trend-researcher`

**Skills** (`.agents/skills/`): `content-queue` · `video-analysis` · `subtitles` · `platform-copywriting` · `social-publishing` (+ per-network playbooks) · `agent-browser-upload` · `content-strategy` · `audience-analytics` · `trend-research` · `community-engagement`

The lead role **asks before writing** for your handles on every network, @mentions, links, fixed hashtags and subtitle preference.

## 🔌 Publishing backends

| Backend | Platforms | Public right away? | Schedules by itself? |
|---|---|---|---|
| `meta_api` | Instagram, Facebook | ✅ | Facebook ✅ |
| `youtube_api` | YouTube | after Google's API audit | ✅ `publishAt` |
| `tiktok_api` | TikTok | after TikTok's audit | — |
| `postiz` | all | ✅ | ✅ (PC can be off) |
| `browser` | all | ✅ | — |
| `handoff` | all | the agent does it | — |

Credentials: [`docs/accounts.md`](docs/accounts.md). They live in `secrets/` (git-ignored).

## 📁 Layout

```
content/inbox/        drop new videos here
content/queue/        YYYY-MM-DD/ (or YYYY-Www/) + <video>.post.yaml
content/published/    archive with receipts      content/library/  raw takes, rendered versions
brand/                voice, audience, hashtags  config/           social.yaml, browser flows, MCP servers
mcp/social-forge/     the MCP + CLI (domain → services → app → server/cli)
.agents/              portable skills and roles  scripts/          bootstrap, install-mcp, schedule, sync
```

## 🧪 Development

```bash
cd mcp/social-forge && uv run pytest     # 46 tests, no network (HTTP shapes mocked, real ffmpeg)
python scripts/sync.py                   # after editing .agents/ or config/
git config core.hooksPath .githooks      # strips AI co-author trailers from commit messages
```

Architecture rules and how to add a backend: [`AGENTS.md`](AGENTS.md).

## ⚠️ Good to know

- TikTok and YouTube **API** uploads stay private until each platform audits your app — use `browser` or `postiz` meanwhile.
- Instagram's API has no publish time: it posts at 05:00 itself, so the PC must be on (or use Postiz).
- Never double-posts: every upload writes a receipt; retries only touch what failed.
- Currently configured for **Chomi la ardilla** 🐿️ — a new brand only needs `brand/` and `config/social.yaml`.

<div align="center"><sub>Made with care for creators who'd rather film than fiddle with schedulers.</sub></div>
