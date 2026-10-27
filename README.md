<a id="top"></a>

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/banner-en-dark.svg">
  <img src="assets/readme/banner-en-light.svg" alt="social-publisher-mcp — An AI community manager for short-form video" width="100%">
</picture>

<br/>

[![tests](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio%20%C2%B7%20HTTP-8A2BE2)
![Docker](https://img.shields.io/badge/Docker-optional-2496ED?logo=docker&logoColor=white)
![platforms](https://img.shields.io/badge/TikTok%20·%20Reels%20·%20Facebook%20·%20Shorts-ff3b5c)
![OS](https://img.shields.io/badge/Windows%20·%20macOS%20·%20Linux-555)

**English** · [Español](README.es.md)

</div>

<p align="center">
<a href="#-what-it-does"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-what-it-does-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-what-it-does-outline-sm-light.svg" alt="What it does" height="34" /></picture></a>
<a href="#-works-with-every-agent"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-works-with-every-agent-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-works-with-every-agent-outline-sm-light.svg" alt="Works with every agent" height="34" /></picture></a>
<a href="#-quick-start"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-quick-start-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-quick-start-outline-sm-light.svg" alt="Quick start" height="34" /></picture></a>
<a href="#-how-a-video-flows"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-how-a-video-flows-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-how-a-video-flows-outline-sm-light.svg" alt="How a video flows" height="34" /></picture></a>
<a href="#-mcp-tools-15"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-mcp-tools-15-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-mcp-tools-15-outline-sm-light.svg" alt="MCP tools (15)" height="34" /></picture></a>
<a href="#-roles-and-skills"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-roles-and-skills-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-roles-and-skills-outline-sm-light.svg" alt="Roles and skills" height="34" /></picture></a>
<a href="#-publishing-backends"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-publishing-backends-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-publishing-backends-outline-sm-light.svg" alt="Publishing backends" height="34" /></picture></a>
<a href="#-layout"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-layout-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-layout-outline-sm-light.svg" alt="Layout" height="34" /></picture></a>
<a href="#-development"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-development-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-development-outline-sm-light.svg" alt="Development" height="34" /></picture></a>
<a href="#-good-to-know"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-good-to-know-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-good-to-know-outline-sm-light.svg" alt="Good to know" height="34" /></picture></a>
</p>

<a id="-what-it-does"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> What it does

| | |
|---|---|
| <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" /> **Dated queue** | `content/queue/2026-10-27/*.mp4` goes out on Oct 27. Three videos in the folder = three posts at 05:00. Week folders (`2026-W44/`) are spread over the days for you. |
| <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" /> **Watches every video** | 8-frame contact sheet + Spanish/any-language transcript (faster-whisper) → it knows what happens, whether there is speech and whether subtitles are already burned in. |
| <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" /> **Per-platform copy** | Hook, body, CTA, hashtags and keywords tuned for TikTok, Instagram Reels, Facebook Reels and YouTube Shorts, validated against each platform's real limits. |
| <img src="assets/readme-builder/icons/repeat.svg" width="20" height="20" alt="" /> **Cross-promotion footer** | Every caption ends with `📲 Follow us too:` and your handles on the *other* networks — automatically. |
| <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" /> **Subtitles** | Decides none / platform auto-captions / `.srt` / burned-in, and renders burned subtitles styled for vertical video. |
| <img src="assets/readme-builder/icons/rocket.svg" width="20" height="20" alt="" /> **Publishes any way it can** | Official APIs (Meta, YouTube, TikTok) → Postiz → a Playwright browser profile → handing the task to the agent itself (Claude in Chrome, Playwright MCP, computer use). |
| ⏰ **05:00 every day** | A Windows scheduled task (cron on macOS/Linux) runs the idempotent publisher with retries, wakes the PC and catches up if it was off. |
| <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" /> **Learns** | Pulls metrics, finds the best weekdays and top/bottom videos, and writes a weekly report with at most three actions. |

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-quick-start"></a>
## <img src="assets/readme-builder/icons/rocket.svg" width="24" height="24" alt="" /> Quick start

```powershell
git clone https://github.com/robgallardof/social-publisher-mcp.git
cd social-publisher-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1        # env, tests, configs, MCP
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 # daily 05:00 task
```

macOS / Linux: `sh scripts/bootstrap.sh` and the cron line printed at the end. Requires [uv](https://docs.astral.sh/uv/).

### Connect your agent

Use this server from OpenCode or DeepSeek Harness. Preview the configuration first, then apply it.

```sh
python scripts/install-mcp.py --clients opencode --dry-run
python scripts/install-mcp.py --clients opencode
opencode mcp list
```

<details>
<summary>Use DeepSeek Harness instead</summary>

```sh
python scripts/install-mcp.py --clients deepseek --dry-run
python scripts/install-mcp.py --clients deepseek
dsh web --patch .dsh/mcp.cordis.yml
```

</details>

[Configuration, removal and tested versions](scripts/CLIENTS.md).

**Prefer Docker?** Optional: the image holds only the MCP code and your folder is mounted at run time.

```bash
docker build -t social-forge:local .
docker run --rm -i -v "C:/path/to/social-publisher-mcp:/workspace" social-forge:local     # stdio, for MCP clients
export SOCIAL_FORGE_MCP_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SOCIAL_FORGE_PORT=8766
docker compose up -d --build --wait social-forge   # HTTP with a token
```

Ports, extras (`analysis`), the CLI service and scheduling `run-due` from the host are in [docs/DOCKER.md](docs/DOCKER.md).

Then talk to your agent:

> *"Process the inbox"* · *"Prepare tomorrow"* · *"Spread week 44, two per day"* · *"Add subtitles to the storytime"* · *"What worked this week?"* · *"Find squirrel trends in Mexico"*

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-works-with-every-agent"></a>
## <img src="assets/readme-builder/icons/bot.svg" width="24" height="24" alt="" /> Works with every agent

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

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-how-a-video-flows"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> How a video flows

<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/diagrams/publishing-en-dark.svg" /><img src="assets/readme/diagrams/publishing-en-light.svg" alt="A practical usage path, generated with Archify" width="100%" /></picture></p>


<details>
<summary>Implementation diagram</summary>

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

</details>

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-roles-and-skills"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Roles and skills

**Roles** (`.agents/agents/`): `community-manager` (lead) · `video-analyst` · `content-strategist` · `copywriter` · `publisher` · `audience-analyst` · `trend-researcher`

**Skills** (`.agents/skills/`): `content-queue` · `video-analysis` · `subtitles` · `platform-copywriting` · `social-publishing` (+ per-network playbooks) · `agent-browser-upload` · `content-strategy` · `audience-analytics` · `trend-research` · `community-engagement`

The lead role **asks before writing** for your handles on every network, @mentions, links, fixed hashtags and subtitle preference.

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-mcp-tools-15"></a>
## <img src="assets/readme-builder/icons/bot.svg" width="24" height="24" alt="" /> MCP tools (15)

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

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-publishing-backends"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Publishing backends

| Backend | Platforms | Public right away? | Schedules by itself? |
|---|---|---|---|
| `meta_api` | Instagram, Facebook | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> | Facebook <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> |
| `youtube_api` | YouTube | after Google's API audit | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> `publishAt` |
| `tiktok_api` | TikTok | after TikTok's audit | — |
| `postiz` | all | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> (PC can be off) |
| `browser` | all | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> | — |
| `handoff` | all | the agent does it | — |

Credentials: [`docs/accounts.md`](docs/accounts.md). They live in `secrets/` (git-ignored).

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-layout"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Layout

```
content/inbox/        drop new videos here
content/queue/        YYYY-MM-DD/ (or YYYY-Www/) + <video>.post.yaml
content/published/    archive with receipts      content/library/  raw takes, rendered versions
brand/                voice, audience, hashtags  config/           social.yaml, browser flows, MCP servers
mcp/social-forge/     the MCP + CLI (domain → services → app → server/cli)
Dockerfile, compose.yaml   optional image (stdio or HTTP with a token)
.agents/              portable skills and roles  scripts/          bootstrap, install-mcp, schedule, sync
```

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-good-to-know"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Good to know

- TikTok and YouTube **API** uploads stay private until each platform audits your app — use `browser` or `postiz` meanwhile.
- Instagram's API has no publish time: it posts at 05:00 itself, so the PC must be on (or use Postiz).
- Never double-posts: every upload writes a receipt; retries only touch what failed.
- Currently configured for **Chomi la ardilla** <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" /> — a new brand only needs `brand/` and `config/social.yaml`.

<div align="center"><sub>Made with care for creators who'd rather film than fiddle with schedulers.</sub></div>

<br/>

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-development"></a>
## <img src="assets/readme-builder/icons/code.svg" width="24" height="24" alt="" /> Development

```bash
cd mcp/social-forge && uv run pytest     # 53 tests: no network, real ffmpeg, real MCP over HTTP
python scripts/test_docker.py            # real image: stdio, CLI, HTTP with token, no personal data
python scripts/sync.py                   # after editing .agents/ or config/
git config core.hooksPath .githooks      # strips AI co-author trailers from commit messages
```

Architecture rules and how to add a backend: [`AGENTS.md`](AGENTS.md).

<p align="center"><a href="#top"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-back-to-top-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-back-to-top-outline-sm-light.svg" alt="Back to top" height="34" /></picture></a></p>

<!-- readme-builder:signature:start -->
<p align="center"><a href="https://github.com/robgallardof"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/brand/signature-en-dark.svg" /><img src="assets/readme/brand/signature-en-light.svg" alt="Social Forge / Roberto Gallardo" width="100%" /></picture></a></p>
<!-- readme-builder:signature:end -->
