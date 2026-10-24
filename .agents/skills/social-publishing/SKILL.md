---
name: social-publishing
description: "How videos get uploaded and scheduled to TikTok, Instagram Reels, Facebook Reels and YouTube Shorts: the backends (official APIs, Postiz, Playwright browser profile, handoff to an agent), the 05:00 scheduled task, modes at_time vs ahead, dry runs, credentials, API limits and how to fix failures. Use it for any upload, scheduling, login or 'it did not post' question."
---

# Social publishing

Tools (MCP `social-forge`): `backends_status` · `publish_due(dry_run)` · `publish_now(video, dry_run)` ·
`mark_published` · `queue_status`. CLI: `uv run social-forge run-due|doctor|status|auth youtube|login <platform>`
(from `mcp/social-forge`). Account setup: `docs/accounts.md`.

Per-network playbooks (paths, gotchas, captions, subtitles): `references/facebook.md`, `references/instagram.md`,
`references/tiktok.md`, `references/youtube.md`.

## Backends (config/social.yaml → `backends: {platform: backend}`)

| Backend | Platforms | Public posts? | Schedules by itself? | Needs |
|---|---|---|---|---|
| `youtube_api` | YouTube | only after Google API audit (else private) | yes (`publishAt`) | OAuth client + `auth youtube` |
| `meta_api` | Instagram, Facebook | yes | Facebook yes, Instagram no | Meta app, IG Business linked to a Page, token |
| `tiktok_api` | TikTok | only after TikTok audit (else SELF_ONLY) | no | TikTok developer app, `video.publish` |
| `postiz` | all four (+X, LinkedIn, Threads… in Postiz) | yes (Postiz's connections) | yes | Postiz cloud or self-hosted + API key |
| `browser` | all four | yes | no (posts at run time) | `login <platform>` once; PC on, user session |
| `handoff` | all | — | no | an agent with computer use / Chrome, or you |

**Recommended start (no app reviews):** `youtube: browser|postiz`, `instagram/facebook: meta_api`, `tiktok: browser`.
Switch YouTube/TikTok to the official API after their audits; or put everything on `postiz` when the PC
cannot be on at 05:00.

## Modes
- `at_time` (default): the Windows task fires at 05:00 (+retries) and publishes that day's videos. The task wakes
  the PC; it needs "allow wake timers" and the user logged in (browser backend opens a real Chrome window).
- `ahead`: the run also uploads videos up to `ahead_days` early to backends that schedule natively
  (YouTube API, Facebook, Postiz). Use it with `postiz` for a PC-off setup.

## Steps
1. `backends_status` → fix whatever is not `ready`.
2. `publish_due(dry_run=true)` → read `do` per line: `publish`, `schedule`, `wait`, `skip` (+`why`), `give_up`.
3. Real run only from the scheduled task or with the user's explicit OK.
4. Report from receipts: platform, status, url/id. `handoff` → `agent-browser-upload`, then `mark_published`.

## Failures
| Symptom | Fix |
|---|---|
| `missing secrets/...` | follow `docs/accounts.md` for that backend |
| YouTube `invalid_grant` / token expired | `uv run social-forge auth youtube` (Testing-mode OAuth apps expire tokens in 7 days: publish the OAuth app) |
| Meta `Invalid OAuth access token` / `Session has expired` | new long-lived token (60 days) or a System User token (never expires) |
| Meta `Application request limit` / 50 posts | wait; IG 50 API posts/24 h, FB Reels 30/24 h |
| TikTok `unaudited_client_can_only_post_to_private_accounts` | use `browser`/`postiz` for TikTok until the audit |
| browser `step N (...) Timeout` | open the screenshot in `content/handoff/screenshots/`, fix `config/browser_flows.yaml`; if it is a login page: `social-forge login <platform>` |
| video rejected (duration/format) | `check_video`; Facebook Reels max 90 s, Shorts max 180 s |

## Install the daily task
`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1` (`-WithAgentPrep` adds a 21:00
headless Claude Code run that writes missing copy; `-Remove` deletes both). macOS/Linux: cron line in `scripts/bootstrap.sh`.
