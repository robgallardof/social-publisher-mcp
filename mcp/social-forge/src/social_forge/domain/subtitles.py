"""Subtitle rules for vertical video. Pure: transcript segments in, SRT text and decisions out."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

MAX_LINE = 32        # chars per line: readable on a phone held upright
MAX_LINES = 2
MIN_WORDS_SPEECH = 6 # fewer recognised words than this = no real speech (music, noises, a lone "trakaaa")


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


def has_speech(segments: list[Segment]) -> bool:
    return sum(len(s.text.split()) for s in segments) >= MIN_WORDS_SPEECH


def _timestamp(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def chunk(segments: list[Segment]) -> list[Segment]:
    """Split long segments so every cue fits MAX_LINES x MAX_LINE, timing split by characters."""
    out = []
    for seg in segments:
        lines = textwrap.wrap(seg.text.strip(), MAX_LINE)
        if not lines:
            continue
        groups = [lines[i:i + MAX_LINES] for i in range(0, len(lines), MAX_LINES)]
        total = sum(len(" ".join(g)) for g in groups)
        t = seg.start
        for g in groups:
            text = "\n".join(g)
            dur = (seg.end - seg.start) * len(" ".join(g)) / total
            out.append(Segment(t, t + dur, text))
            t += dur
    return out


def to_srt(segments: list[Segment]) -> str:
    cues = chunk(segments)
    return "".join(f"{i}\n{_timestamp(c.start)} --> {_timestamp(c.end)}\n{c.text}\n\n"
                   for i, c in enumerate(cues, 1))
