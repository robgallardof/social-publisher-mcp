---
name: platform-copywriting
description: "Write titles, captions, hashtags and keywords for TikTok, Instagram Reels, Facebook Reels and YouTube Shorts: per-platform limits and search behaviour, hook formulas for the first line, CTA, hashtag strategy, Spanish/LatAm style. Use it whenever writing or reviewing any social description, title or hashtag set."
---

# Platform copywriting

Hard limits: `references/platforms.md` (generated from code; `preview_post` enforces them).
Formulas and examples: `references/formulas.md`.

## What each platform reads

| | TikTok | Instagram Reels | Facebook Reels | YouTube Shorts |
|---|---|---|---|---|
| Search | Strong: caption words + on-screen text + speech are indexed | Keywords in caption beat hashtags | Weak | Title is the main search field |
| First line | Shown ~1-2 lines: hook | ~125 chars before "more" | Short, conversational | Title ≤ 70 chars visible; description rarely seen |
| Hashtags | 3-5 (cap 5) | 3-5 specific | 0-3 | 2-3; first 3 show above the title |
| Tone | Casual, inside jokes | Aesthetic/useful, saves | Broader, older audience, plain language | Searchable, descriptive |
| CTA that works | question to answer in comments, "part 2?" | "save this", "send it to…" | "share with…" | "subscribe for part 2" sparingly |

## Method (per video)
1. **One idea, one keyword.** What would someone type to find this? Use it in the title (YouTube), the first
   caption line (Instagram/TikTok) and say it in the video if you are briefing the editor.
2. **Hook line** (≤ 125 chars): curiosity gap, stakes, a contradiction, a number or a direct "you".
   It must match the video's first 2 seconds (mismatch kills retention).
3. **Body** (optional, 1-2 lines): context the video does not give; line breaks; 0-2 emojis that add meaning.
4. **CTA**: one, specific, natural. Questions that people genuinely want to answer beat "comment below".
5. **Hashtags**: 1 niche (#humorgatuno) + 1-2 topic (#gatos) + 1 community/format (#mascotasdetiktok) + optional 1 broad.
   No #fyp/#viral walls; no banned or unrelated tags. Rotate: `brand/hashtags.md` has the bank.
6. **YouTube**: `title` keyword-first, no ALL CAPS, `<`/`>` forbidden; `tags` = search variants (misspellings ok), ≤ 500 chars.
7. Check `preview_post`: fix every `problems` item; read each platform's final text once as a viewer.

## Brand footer (cross-promotion)
Every caption ends with the other networks' handles, generated from `config/social.yaml` → `brand.handles`:
```
<body>

📲 Síguenos también:
Instagram: @chomiescuincla
TikTok: @andrearuizdmn

#chomilaardilla #ardilla
```
The platform being posted to is left out of its own footer. Missing handles → ask the user (never invent them).

## Spanish / LatAm notes
Neutral Mexican Spanish unless `brand/voice.md` says otherwise; ¿¡ opening marks; avoid regional slang that
excludes the rest of LatAm unless it is the brand. Hashtags without accents get more matches (#cocinafacil and
#cocinafácil are different tags: use the one with more posts in the platform search).

## Never
Promise what the video does not show; copy another creator's caption; post the identical caption on many videos;
mention brands/people/prices/health claims that the user did not give you; hide paid partnerships.
