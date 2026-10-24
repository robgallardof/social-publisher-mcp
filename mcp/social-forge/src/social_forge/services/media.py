"""Read a video's real duration/size with the bundled ffmpeg and check it against each platform."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..domain import platforms


@dataclass(frozen=True)
class Probe:
    duration_s: float
    width: int
    height: int
    size_mb: float

    @property
    def vertical(self) -> bool:
        return self.height > self.width


def probe(video: Path) -> Probe:
    import imageio_ffmpeg

    out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(video)],
                         capture_output=True, text=True, stdin=subprocess.DEVNULL,
                         encoding="utf-8", errors="replace").stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    res = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", out)
    if not dur or not res:
        raise ValueError(f"not a readable video: {video.name}")
    h, m, s = dur.groups()
    rotated = re.search(r"rotate\s*:\s*-?(90|270)", out) or re.search(r"rotation of -?(90|270)", out)
    w, ht = int(res[1]), int(res[2])
    if rotated:
        w, ht = ht, w
    return Probe(int(h) * 3600 + int(m) * 60 + float(s), w, ht, round(video.stat().st_size / 1e6, 1))


def check(p: Probe, platform: str) -> tuple[list[str], list[str]]:
    """(errors, warnings) of a probed file for one platform."""
    spec = platforms.get(platform)
    errors, warnings = [], []
    if p.duration_s < spec.min_duration_s:
        errors.append(f"{p.duration_s:.1f}s shorter than {spec.min_duration_s:g}s")
    if p.duration_s > spec.max_duration_s:
        errors.append(f"{p.duration_s:.1f}s longer than {spec.max_duration_s:g}s for {spec.name}")
    if not p.vertical:
        warnings.append(f"{p.width}x{p.height} is not vertical; {spec.name} wants {spec.aspect}")
    if max(p.width, p.height) < 1280:
        warnings.append(f"low resolution {p.width}x{p.height}; target {spec.resolution}")
    return errors, warnings
