---
name: video-analysis
description: "Understand a video before writing about it or scheduling it: contact sheet of frames, speech transcript (faster-whisper), whether it has speech, burned-in text, music vs dialogue, duration and format, and a one-line summary saved in the .post.yaml. Use it for every new video in content/inbox or the queue, and whenever asked what a video is about."
---

# Video analysis

Tool: `analyze_video(video)` (MCP social-forge; extra `analysis`). Accepts a name anywhere under `content/`
or an absolute path. Writes to `analytics/videos/<stem>/`: `frames.jpg`, `transcript.txt`, `<stem>.srt`.

## Method (per video)
1. `analyze_video` → read `duration_s`, `size`, `speech`, `transcript`.
2. **Open `frames.jpg` and look** (Read tool / image viewer). Note: who is on screen, what happens, setting,
   on-screen text (POV lines, memes), burned subtitles (karaoke words at the bottom = already subtitled).
3. Decide the type: talking to camera / storytime · meme or lip-sync audio · music montage · silent/ambient.
   A transcript of song lyrics or a famous audio means *music/meme*, not dialogue (e.g. "Ardillas por doquier").
4. Decide subtitles (skill `subtitles`): none | auto | burned | srt.
5. Write one-sentence `summary` + `speech` + subtitles into `write_post(..., subtitles=..., analysis_notes={...})`.
6. Raw/full takes and duplicates go to `content/library/`; only edited cuts go to the queue.

## Pitfalls
- Two files can look alike (two cleaning videos): tell them apart by on-screen text and audio, not just frames.
- Whisper invents words on music; trust the frames for what happens and the transcript only for real speech.
- iPhone .mov (HEVC, 1080x1920) is fine for Facebook; check `check_video` limits for other platforms.
- Never describe something not visible or audible in the video.
