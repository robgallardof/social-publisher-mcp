import importlib.util
import json
from pathlib import Path

import pytest
from conftest import add_video, at
from test_media_and_server import make_clip

from social_forge.domain import post, subtitles
from social_forge.domain.subtitles import Segment
from social_forge.services import analysis, queue, runner

ROOT = Path(__file__).resolve().parents[3]
BRAND = post.Brand.from_dict({"handles": {"facebook": "Chomi la ardilla", "instagram": "@chomiescuincla",
                                          "tiktok": "andrearuizdmn"}})


def test_footer_lists_the_other_networks_only():
    assert BRAND.footer("facebook") == "📲 Síguenos también:\nInstagram: @chomiescuincla\nTikTok: @andrearuizdmn"
    assert "Instagram" not in BRAND.footer("instagram") and "Facebook: Chomi la ardilla" in BRAND.footer("instagram")
    assert post.Brand.from_dict({"handles": {"instagram": ""}}).footer("facebook") == ""


def test_render_order_body_footer_hashtags_and_opt_out():
    spec = post.PostSpec.from_dict({"caption": "Hola", "hashtags": ["ardilla"]})
    assert post.render(spec, "facebook", BRAND).caption == (
        "Hola\n\n📲 Síguenos también:\nInstagram: @chomiescuincla\nTikTok: @andrearuizdmn\n\n#ardilla")
    off = post.PostSpec.from_dict({"caption": "Hola", "footer": False})
    assert post.render(off, "facebook", BRAND).caption == "Hola"


def test_subtitles_field_validated_and_rendered():
    spec = post.PostSpec.from_dict({"caption": "x", "subtitles": "auto", "overrides": {"tiktok": {"subtitles": "none"}}})
    assert post.render(spec, "facebook").subtitles == "auto" and post.render(spec, "tiktok").subtitles == "none"
    with pytest.raises(ValueError, match="subtitles"):
        post.PostSpec.from_dict({"caption": "x", "subtitles": "yes"})
    assert "subtitles" not in post.PostSpec.from_dict({"caption": "x"}).to_dict()


def test_srt_wraps_for_phone_and_formats_time():
    long = Segment(0.0, 4.0, "esta es una frase bastante larga que no cabe en una sola linea del celular")
    srt = subtitles.to_srt([long, Segment(61.5, 62.25, "ok")])
    cues = srt.strip().split("\n\n")
    assert cues[0].startswith("1\n00:00:00,000 --> ")
    assert all(len(line) <= subtitles.MAX_LINE for c in cues for line in c.split("\n")[2:])
    assert "00:01:01,500 --> 00:01:02,250\nok" in srt
    assert subtitles.has_speech([long]) and not subtitles.has_speech([Segment(0, 1, "trakaaaa")])


def test_contact_sheet_and_burn(tmp_path):
    clip = tmp_path / "v.mp4"
    make_clip(clip, 1080, 1920, 3)
    sheet = analysis.contact_sheet(clip, tmp_path / "sheet.jpg", frames=4, width=120)
    assert sheet.stat().st_size > 0
    srt = analysis.write_srt([Segment(0.2, 2.5, "hola Chomi")], tmp_path / "v.srt")
    out = analysis.burn(clip, srt, tmp_path / "out" / "v.subtitulado.mp4")
    assert out.stat().st_size > 0


@pytest.mark.skipif(importlib.util.find_spec("faster_whisper") is None, reason="analysis extra not installed")
def test_analyze_silent_clip_reports_no_speech(tmp_path):
    clip = tmp_path / "silent.mp4"
    make_clip(clip, 1080, 1920, 2)
    out = analysis.analyze(clip, tmp_path / "work")
    assert out["speech"] is False and out["srt"] is None and Path(out["frames"]).exists()


def test_runner_and_handoff_carry_footer_and_subtitles(settings, ws):
    settings.brand = {"handles": {"instagram": "chomiescuincla", "tiktok": "andrearuizdmn"}}
    settings.default_platforms, settings.backends = ["facebook"], {"facebook": "handoff"}
    add_video(ws, "2026-10-27/a.mp4", {"caption": "Hola", "subtitles": "auto"})
    report = runner.run(settings, at(2026, 10, 27, 5))
    task = Path(report[0]["result"]["task"]).read_text(encoding="utf-8")
    assert "Instagram: @chomiescuincla" in task and "TikTok: @andrearuizdmn" in task
    assert "turn ON the platform's automatic captions" in task
    assert queue.scan(settings.queue_dir)[0].receipts["facebook"]["status"] == "handoff"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_mcp", ROOT / "scripts" / "install-mcp.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_installer_json_toml_roundtrip(tmp_path):
    inst = load_installer()
    j = tmp_path / "mcp.json"
    j.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
    assert inst.edit_json(j, "mcpServers", remove=False) == "installed"
    data = json.loads(j.read_text(encoding="utf-8"))
    assert "other" in data["mcpServers"] and data["mcpServers"]["social-forge"]["env"]["SOCIAL_FORGE_ROOT"]
    assert (tmp_path / "mcp.json.bak").exists()
    assert inst.edit_json(j, "mcpServers", remove=True) == "removed"
    t = tmp_path / "config.toml"
    t.write_text('model = "x"\n\n[mcp_servers.other]\ncommand = "y"\n', encoding="utf-8")
    inst.edit_toml(t, remove=False)
    inst.edit_toml(t, remove=False)  # idempotent
    text = t.read_text(encoding="utf-8")
    assert text.count("[mcp_servers.social-forge]") == 1 and "[mcp_servers.other]" in text
    inst.edit_toml(t, remove=True)
    assert "social-forge" not in t.read_text(encoding="utf-8") and 'model = "x"' in t.read_text(encoding="utf-8")
