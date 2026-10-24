import asyncio
import subprocess

import imageio_ffmpeg

from social_forge.services import media


def make_clip(path, w, h, seconds):
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", f"color=c=black:s={w}x{h}:d={seconds}", "-pix_fmt", "yuv420p", str(path)],
                   check=True, stdin=subprocess.DEVNULL)


def test_probe_and_platform_checks(tmp_path):
    clip = tmp_path / "v.mp4"
    make_clip(clip, 1080, 1920, 2)
    p = media.probe(clip)
    assert (p.width, p.height) == (1080, 1920) and 1.9 < p.duration_s < 2.2
    errors, warnings = media.check(p, "tiktok")
    assert "shorter than 3s" in errors[0] and warnings == []
    wide = tmp_path / "w.mp4"
    make_clip(wide, 640, 360, 4)
    _, warnings = media.check(media.probe(wide), "instagram")
    assert any("not vertical" in w for w in warnings) and any("low resolution" in w for w in warnings)


def test_mcp_server_exposes_tools():
    from social_forge.server import mcp

    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert {"queue_status", "plan_week", "write_post", "preview_post", "publish_due", "publish_now",
            "mark_published", "backends_status", "pull_metrics", "insights_report", "check_video",
            "platform_rules"} <= names
