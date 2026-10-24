# Facebook Page Reels — playbook (verified 2026-10-24, page "Chomi la ardilla", id 1338478969353834)

**Where**: Meta Business Suite `https://business.facebook.com/latest/reels_composer?page_id=<id>&asset_id=<id>`.
Check "Publicar en" shows the Page (switch business asset top-left if it shows another profile).

**Create**: Agregar video (large files: `agent-browser-upload` relay) → Descripción → Siguiente (Editar: audio,
leave) → Siguiente (Compartir) → Programar → date `dd/mm/aaaa`, hour/minutes spinbuttons (24 h, America/Mexico_City)
→ Subtítulos (skill `subtitles`) → Programar → "Tu reel está programado para publicarse el …".

**Edit a scheduled reel**: Contenido → Programadas → row ⋯ → Administrar publicación → Editar reel, or directly
`/latest/edit_composer/?entry_point=biz_web_scheduled_posts&profile_id=<page>&video_id=<video>`.

**Gotcha (cost us one round)**: the description box is a Lexical editor. Text inserted only by script/paste
event shows on screen but is NOT saved. After inserting, send a real keystroke (End, space, Backspace) and click
Siguiente with a real click. Then verify in Programadas that the row shows your text, not "Tu reel".

**Caption**: body · brand footer (`📲 Síguenos también:` + IG/TikTok handles) · 0-3 hashtags. ≤ 2200 chars.
**Limits**: all videos are reels now (2:11 min accepted); HEVC .mov accepted; API: 30 reels / 24 h.
**After publishing**: `mark_published(video, "facebook", url, status="scheduled"|"published")`.
