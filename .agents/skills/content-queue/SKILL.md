---
name: content-queue
description: "The folder of finished videos and how the publisher knows what to post: dated folders (YYYY-MM-DD), week folders (YYYY-Www), the .post.yaml copy file, receipts, archive, and the rule that every video of a day goes out at 05:00. Use it whenever adding, moving, planning or checking queued videos."
---

# Content queue

```
content/inbox/                the user drops new videos here (never the repo root): the agent watches each one
                              (frames + transcript), names it, moves it to a day folder and writes its copy
content/library/              raw/unused material (full takes, versions not to publish)
content/queue/
  2026-10-27/                 every video here goes out on Oct 27 at post_time (05:00)
    01-gato-pepino.mp4
    01-gato-pepino.post.yaml  copy (written by the copywriter)
    01-gato-pepino.mp4.receipts.json   written by the runner, one entry per platform
  2026-W44/                   a week: drop loose videos here...
    clip-a.mp4                ...and plan_week spreads them over the remaining days
    2026-10-29/clip-b.mp4     day folders can also live inside a week folder
content/published/<day>/      archive: video + copy + receipts once every platform is done
content/handoff/              tasks for an agent/person when a platform has no automatic backend
```

- Day = the nearest `YYYY-MM-DD` folder above the file. A video loose in `YYYY-Www` has no day until `plan_week(apply=true)`.
- Same day = same time: 3 videos on Oct 27 → 3 posts at 05:00 (or 05:00/05:10/05:20 with `stagger_minutes: 10`).
  Order inside a day = file name order, so prefix `01-`, `02-` when order matters.
- Formats: .mp4 .mov .m4v .webm. Vertical 1080x1920 (H.264, AAC). See `platform-copywriting/references/platforms.md`.
- Overdue videos (PC was off) are published on the next run when `catch_up: true`.

## Processing the inbox
1. `queue_status` → `inbox` list. For each video: `analyze_video` (8-frame contact sheet, Spanish transcript,
   speech yes/no, .srt) and look at the frames — skill `video-analysis`.
2. Rename to `NN-short-slug.ext` (what it is about), decide the day with `content-strategy`, move it into
   `content/queue/<YYYY-Www>/<YYYY-MM-DD>/`. Edited cuts go to the queue; raw full takes go to `content/library/`.
3. `copywriter` writes the `.post.yaml`. Series (Part 1/Part 2) on consecutive days, Part 1 first.

## The copy file (`<video stem>.post.yaml`)

```yaml
title: "Mi gato vs un pepino"            # YouTube title; on other platforms it becomes the caption's first line
caption: |
  No lo vio venir 😂
  ¿El tuyo también le teme a los pepinos?
hashtags: [gatos, humorgatuno, mascotas]  # '#' optional
platforms: [tiktok, instagram, youtube]   # optional; default = config default_platforms
overrides:                                # optional per-platform changes
  tiktok: {caption: "No lo vio venir 😂 #gatos"}
  youtube: {tags: [gato, pepino, gato asustado]}
publish_time: "05:00"                     # optional; default config post_time
approved: true                            # false = runner waits
footer: true                              # add "Síguenos también" with the other networks' handles
subtitles: auto                           # none | auto | burned | srt  (skill `subtitles`)
analysis: {summary: "...", speech: true}  # from analyze_video (skill `video-analysis`)
```

Write it with `write_post`, check it with `preview_post`. No copy file → the runner skips the video (never posts blank).

## Receipts and retries

`<video>.receipts.json` holds `{platform: {status, id, url, attempts, at, error}}`. `published`, `scheduled` and
`handoff` are never retried; `failed` is retried on the next run until `max_attempts` (3), then flagged.
`mark_published(video, platform, url)` closes a handoff. The scheduled task runs at 05:00, +20 min, +1 h, +2 h.
