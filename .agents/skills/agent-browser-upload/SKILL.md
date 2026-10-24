---
name: agent-browser-upload
description: "Upload a video (or read insights) by driving the browser or desktop yourself — Claude in Chrome, Playwright MCP, Chrome DevTools MCP or computer use — for TikTok Studio, Instagram, Facebook Reels and YouTube Studio. Use it for handoff tasks in content/handoff/, when the browser backend breaks, or to read analytics the APIs do not expose."
---

# Agent-driven upload

Use the strongest tool your runtime has, in this order:
1. **Claude in Chrome** (`mcp__claude-in-chrome__*`): the user's real Chrome, already logged in. Has `file_upload`.
2. **Playwright MCP** (`playwright` in `config/mcp.servers.json`, profile `.profiles/agent`): `browser_file_upload`.
   First time per platform the user logs in inside that window.
3. **Computer use** (desktop screenshots/clicks): last resort, slowest; the native file dialog needs the full path typed.

## Before
- Read the handoff task: video path, exact caption, title, platform. Check receipts: if already published, stop.
- The user must already be logged in. Never type passwords or 2FA codes; if a login wall appears, ask the user.
- Do not trigger browser `alert/confirm` dialogs (they freeze Claude in Chrome); avoid "Discard" buttons.

## Big files with Claude in Chrome (verified 2026-10-24, Facebook Page reels)
`file_upload` is capped at 10 MB and the extension intercepts native file pickers in its tabs; Facebook's CSP
blocks `fetch` to localhost. What works for any size (`scripts/upload-relay/`):
1. `uv run --directory mcp/social-forge python ../../scripts/upload-relay/serve.py ../../content/queue` (background;
   127.0.0.1:8765 only, serves `relay.html` + the queue).
2. On the composer tab inject (javascript_tool): patch `HTMLInputElement.prototype.click` so a file input gets
   `window.__cmFile` via DataTransfer + `change`; a `message` listener (origin `http://127.0.0.1:8765`) that stores
   `e.data.cmFile` and replies `cm-ack`; and a fixed "CM relay" button whose onclick
   `window.open('http://127.0.0.1:8765/relay.html?f=<path inside queue>')`.
3. Click that button with a real (extension) click → the popup loads the file and `postMessage`s the File back.
4. Click "Agregar video" → the patched input receives it. Caption: dispatch a `paste` ClipboardEvent with
   text/plain on the `[contenteditable][aria-label^="Escribe en el cuadro"]` editor (keeps newlines/emojis).
5. Meta Business Suite reel composer (`/latest/reels_composer?page_id=<id>&asset_id=<id>`): Siguiente → Siguiente →
   "Programar" → date textbox `dd/mm/aaaa` (triple-click, type `25/10/2026`, Enter), spinbuttons `horas`/`minutos`
   → "Programar". Confirmation text: "Tu reel está programado para publicarse el …". Then
   `mark_published(video, "facebook", url, status="scheduled")`. Check the list at `/latest/posts/scheduled_posts`.
Use element refs or JS clicks by label, never fixed coordinates (the window can resize mid-run).
**The caption only saves after a real keystroke**: Facebook's editor (Lexical) ignores text that arrives only by a
script/paste event. After pasting press End, type a space, Backspace, and click Siguiente with a real (ref) click;
then confirm in Programadas that the row shows the caption, not "Tu reel". Editing scheduled reels: see
`social-publishing/references/facebook.md`.
Facebook accepts .mov/HEVC as-is; all Facebook videos are reels now (2:11 min went through).

## Flows (labels in English / Spanish UI)
**TikTok** — tiktok.com/tiktokstudio/upload → file input → wait until the caption editor appears → replace the
default caption (file name) with the text → wait "Uploaded/Cargado" → "Post/Publicar" → if asked, "Post now".
Settings to leave as default unless brief says otherwise: Everyone can view, comments on.

**Instagram** — instagram.com → Create (+) → Post → select file → "OK" (video posts become reels) → crop 9:16 →
Next → Next → caption → Share → wait "Your reel has been shared".

**Facebook (Page)** — switch to the Page profile first → facebook.com/reels/create → upload → Next → description → Publish.
Alternative: Meta Business Suite → Create reel (also allows scheduling).

**YouTube** — studio.youtube.com → Create → Upload videos → file → Title (keyword-first), Description →
"No, it's not made for kids" → Next ×3 → Visibility Public (or Schedule with date/time) → Publish/Schedule.
Vertical ≤ 3 min becomes a Short automatically.

## After
- Copy the post URL (profile → newest post). `mark_published(video, platform, url)`.
- Edit the handoff task: `Status: done <url>`.
- If anything looked different from these flows, update `config/browser_flows.yaml` and this file.

## Reading insights (no API)
TikTok Studio → Analytics / each post's analytics; Instagram → Professional dashboard / reel → View insights;
Meta Business Suite → Insights → Content; YouTube Studio → Analytics → Content → Shorts.
Read: views, avg watch time, % watched full, retention drop second, shares, saves, follows from post,
audience top countries/ages, follower active hours. Append to `analytics/audience.md` with date and source.
