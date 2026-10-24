"""Understand a video before writing about it: frames, transcript, speech, subtitles.

Frames come from the bundled ffmpeg; the transcript from faster-whisper (extra `analysis`), fed with raw
PCM decoded by ffmpeg (no PyAV, which breaks across versions). Outputs live in analytics/videos/<stem>/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..domain import subtitles
from ..domain.subtitles import Segment
from . import media

_MODEL = None


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", *args],
                          capture_output=True, stdin=subprocess.DEVNULL)


def contact_sheet(video: Path, out: Path, frames: int = 8, width: int = 240) -> Path:
    """One image with `frames` evenly spaced thumbnails, left to right."""
    duration = media.probe(video).duration_s
    out.parent.mkdir(parents=True, exist_ok=True)
    r = run(["-y", "-i", str(video), "-vf", f"fps={frames / max(duration, 0.1):.6f},scale={width}:-2,tile={frames}x1",
             "-frames:v", "1", str(out)])
    if r.returncode or not out.exists():
        raise RuntimeError(f"contact sheet failed: {r.stderr.decode(errors='replace')[:300]}")
    return out


def _model(size: str):
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel

        _MODEL = WhisperModel(size, device="cpu", compute_type="int8")  # CUDA DLLs are often missing on Windows
    return _MODEL


def transcribe(video: Path, language: str = "es", size: str = "small") -> list[Segment]:
    import numpy as np

    pcm = run(["-i", str(video), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]).stdout
    if not pcm:
        return []
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = _model(size).transcribe(audio, language=language, vad_filter=True)
    return [Segment(s.start, s.end, s.text.strip()) for s in segs if s.text.strip()]


def write_srt(segments: list[Segment], path: Path) -> Path:
    path.write_text(subtitles.to_srt(segments), encoding="utf-8")
    return path


def burn(video: Path, srt: Path, out: Path) -> Path:
    """Render subtitles into the picture (white, black outline, lower third above the app UI)."""
    style = ("FontName=Arial,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=70")
    # ffmpeg's subtitles filter needs the path escaped (Windows drive colon, backslashes)
    escaped = srt.resolve().as_posix().replace(":", r"\:")
    out.parent.mkdir(parents=True, exist_ok=True)
    r = run(["-y", "-i", str(video), "-vf", f"subtitles='{escaped}':force_style='{style}'",
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", str(out)])
    if r.returncode or not out.exists():
        raise RuntimeError(f"burn failed: {r.stderr.decode(errors='replace')[:300]}")
    return out


def analyze(video: Path, workdir: Path, language: str = "es") -> dict:
    """Everything the copywriter needs, plus files to look at."""
    p = media.probe(video)
    folder = workdir / video.stem
    sheet = contact_sheet(video, folder / "frames.jpg")
    try:
        segs = transcribe(video, language)
        transcript_error = None
    except ImportError:
        segs, transcript_error = [], "install extras: uv sync --extra analysis"
    text = " ".join(s.text for s in segs)
    (folder / "transcript.txt").write_text(text, encoding="utf-8")
    speech = subtitles.has_speech(segs)
    srt = write_srt(segs, folder / f"{video.stem}.srt") if speech else None
    return {"video": str(video), "duration_s": round(p.duration_s, 2), "size": f"{p.width}x{p.height}",
            "frames": str(sheet), "transcript": text, "speech": speech, "srt": str(srt) if srt else None,
            "transcript_error": transcript_error,
            "next": "Open `frames` and look: are subtitles/text already burned in? Then set subtitles in "
                    "write_post: none (no speech or already on screen) | auto (turn on platform captions) | "
                    "burned (make_subtitles burn=true) | srt (upload the .srt where the platform allows)."}
