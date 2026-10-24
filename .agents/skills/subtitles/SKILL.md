---
name: subtitles
description: "Decide and apply subtitles/captions for short videos on Facebook, Instagram, TikTok and YouTube: when a video needs them, platform automatic captions vs uploading an .srt vs burning them into the picture, style for vertical video, and how to switch them on in each app. Use it whenever a video has speech, when asked about subtitles/captions/subtítulos, or before scheduling."
---

# Subtitles

Most short-video viewers watch muted: **every video with dialogue needs subtitles**. Videos with no speech
(music, ambient) or with the words already on screen do not.

## Decision (store it as `subtitles:` in the .post.yaml)
| Situation | Mode | Action |
|---|---|---|
| No speech, or music/lyrics only | `none` | nothing |
| Words already burned in (karaoke captions, meme text that carries the dialogue) | `burned` | nothing |
| Speech without subtitles, quick path | `auto` | turn on the platform's automatic captions when uploading/editing |
| Speech, accuracy matters (names, slang, Spanish) and the platform takes files | `srt` | `make_subtitles(video)` → upload the .srt |
| Speech and you want them everywhere identically (TikTok/IG don't take .srt) | `burned` | `make_subtitles(video, burn=true)` → review the copy in `content/library/` → swap it into the queue |

Burned style (built into `make_subtitles`): white bold, black outline, ≤ 32 chars × 2 lines, lower third
above the app buttons (MarginV 70 on 1920 px). Check that they don't cover faces in `frames.jpg` of the output.

## Per platform
- **Facebook (Business Suite reel composer / Editar reel)**: step *Compartir* → section *Subtítulos* → tick
  "Aplica subtítulos a tu video" → shows "Subtítulos automáticos activados"; *Configurar* lets you review or
  upload an .srt. Works on scheduled reels via Contenido → Programadas → ⋯ → Administrar publicación → Editar reel.
- **Instagram**: Reels get auto-generated captions that viewers toggle; in the app before sharing: Advanced
  settings → "Show captions"/auto captions on. No .srt upload → burn when accuracy matters.
- **TikTok**: TikTok Studio / app → "Captions" (auto) after upload, editable before posting. No .srt → burn for
  exact wording.
- **YouTube Shorts**: Studio → Subtitles → upload the .srt (best) or auto-captions (auto, slower to appear).

## Verify
After saving, reopen the post editor and confirm the caption state persisted ("Subtítulos automáticos activados").
Record the mode in the .post.yaml so the next agent knows.
