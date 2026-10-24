"""Official-API publishers against recorded HTTP shapes (httpx.MockTransport): no network."""

import json
from pathlib import Path

import httpx
import pytest
from conftest import at

from social_forge.domain.post import Copy
from social_forge.services import secrets
from social_forge.services.publishers import Job, PublisherError, browser, build, handoff, meta, postiz, tiktok, youtube

MB = 1024 * 1024


def job(tmp_path: Path, platform: str, when, title=None) -> Job:
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"v" * 2048)
    return Job(video, Copy(platform, "Texto #tag", title, ("tag",)), when)


def recorder(handler):
    seen = []

    def wrapped(request: httpx.Request):
        seen.append(request)
        return handler(request)
    return httpx.Client(transport=httpx.MockTransport(wrapped)), seen


def test_tiktok_chunk_rules():
    assert tiktok.chunks(10 * MB) == [(0, 10 * MB - 1)]
    big = tiktok.chunks(95 * MB)
    assert len(big) == 9 and big[-1] == (80 * MB, 95 * MB - 1)


def test_meta_instagram_flow(settings, tmp_path):
    settings.accounts["meta"] = {"ig_user_id": "17", "graph_version": "v24.0"}
    secrets.save(settings, "meta", {"access_token": "T", "page_access_token": "P"})

    def handler(r: httpx.Request):
        if r.url.path.endswith("/17/media"):
            return httpx.Response(200, json={"id": "C1"})
        if r.url.host == "rupload.facebook.com":
            assert r.headers["Authorization"] == "OAuth T" and r.headers["file_size"] == "2048"
            return httpx.Response(200, json={"success": True})
        if r.url.path.endswith("/C1"):
            return httpx.Response(200, json={"status_code": "FINISHED"})
        if r.url.path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "M9"})
        return httpx.Response(200, json={"permalink": "https://instagram.com/reel/x"})
    http, seen = recorder(handler)
    out = meta.MetaApi(settings, "instagram", http, sleep=lambda s: None).publish(
        job(tmp_path, "instagram", at(2026, 10, 27, 5)), at(2026, 10, 27, 5))
    assert out == {"status": "published", "id": "M9", "url": "https://instagram.com/reel/x"}
    assert "media_type=REELS" in seen[0].content.decode() and "upload_type=resumable" in seen[0].content.decode()


def test_meta_facebook_schedules_natively(settings, tmp_path):
    settings.accounts["meta"] = {"page_id": "55"}
    secrets.save(settings, "meta", {"access_token": "T", "page_access_token": "P"})

    def handler(r: httpx.Request):
        if r.url.host == "rupload.facebook.com":
            return httpx.Response(200, json={"success": True})
        body = r.content.decode()
        return httpx.Response(200, json={"video_id": "V1"} if "start" in body else {"success": True})
    http, seen = recorder(handler)
    out = meta.MetaApi(settings, "facebook", http).publish(
        job(tmp_path, "facebook", at(2026, 10, 28, 5)), at(2026, 10, 27, 21))
    assert out["status"] == "scheduled"
    finish = seen[-1].content.decode()
    assert "video_state=SCHEDULED" in finish and "scheduled_publish_time=" in finish


def test_meta_error_message_surfaces(settings, tmp_path):
    settings.accounts["meta"] = {"ig_user_id": "17"}
    secrets.save(settings, "meta", {"access_token": "T"})
    http, _ = recorder(lambda r: httpx.Response(400, json={"error": {"message": "Invalid token"}}))
    with pytest.raises(PublisherError, match="Invalid token"):
        meta.MetaApi(settings, "instagram", http).publish(job(tmp_path, "instagram", at(2026, 10, 27, 5)),
                                                          at(2026, 10, 27, 5))


def test_tiktok_direct_post_respects_privacy_options(settings, tmp_path):
    secrets.save(settings, "tiktok", {"access_token": "A"})

    def handler(r: httpx.Request):
        if r.url.path.endswith("creator_info/query/"):
            return httpx.Response(200, json={"data": {"privacy_level_options": ["SELF_ONLY"]}, "error": {"code": "ok"}})
        if r.url.path.endswith("video/init/"):
            return httpx.Response(200, json={"data": {"publish_id": "P1", "upload_url": "https://up.tiktok/u"},
                                             "error": {"code": "ok"}})
        if r.method == "PUT":
            assert r.headers["Content-Range"] == "bytes 0-2047/2048"
            return httpx.Response(201)
        return httpx.Response(200, json={"data": {"status": "PUBLISH_COMPLETE",
                                                  "publicaly_available_post_id": [7]}, "error": {"code": "ok"}})
    http, seen = recorder(handler)
    out = tiktok.TikTokApi(settings, http, sleep=lambda s: None).publish(
        job(tmp_path, "tiktok", at(2026, 10, 27, 5)), at(2026, 10, 27, 5))
    assert out["privacy"] == "SELF_ONLY" and out["id"] == "7"
    init = json.loads(seen[1].content)
    assert init["source_info"] == {"source": "FILE_UPLOAD", "video_size": 2048, "chunk_size": 2048,
                                   "total_chunk_count": 1}


def test_postiz_schedules_with_provider_settings(settings, tmp_path):
    settings.accounts["postiz"] = {"url": "https://pz.local/api/public/v1", "integrations": {"youtube": "I1"}}
    secrets.save(settings, "postiz", {"api_key": "K"})

    def handler(r: httpx.Request):
        assert r.headers["Authorization"] == "K"
        if r.url.path.endswith("/upload"):
            return httpx.Response(200, json={"id": "U", "path": "https://pz.local/u.mp4"})
        return httpx.Response(200, json=[{"postId": "PP"}])
    http, seen = recorder(handler)
    out = postiz.Postiz(settings, "youtube", http).publish(
        job(tmp_path, "youtube", at(2026, 10, 28, 5), title="Titulo"), at(2026, 10, 27, 21))
    body = json.loads(seen[-1].content)
    assert out["status"] == "scheduled" and body["type"] == "schedule" and body["date"] == "2026-10-28T11:00:00Z"
    assert body["posts"][0]["settings"]["__type"] == "youtube" and body["posts"][0]["settings"]["title"] == "Titulo"


def test_youtube_body_uses_publish_at_only_in_future(settings, tmp_path):
    yt = youtube.YouTubeApi(settings)
    later = yt.body(job(tmp_path, "youtube", at(2026, 10, 28, 5), "T"), at(2026, 10, 27, 21))
    assert later["status"] == {"selfDeclaredMadeForKids": False, "privacyStatus": "private",
                               "publishAt": "2026-10-28T11:00:00Z"}
    now = yt.body(job(tmp_path, "youtube", at(2026, 10, 28, 5), "T"), at(2026, 10, 28, 5))
    assert now["status"]["privacyStatus"] == "public"


def test_handoff_writes_task(settings, tmp_path):
    out = handoff.Handoff(settings).publish(job(tmp_path, "tiktok", at(2026, 10, 27, 5)), at(2026, 10, 27, 5))
    text = Path(out["task"]).read_text(encoding="utf-8")
    assert out["status"] == "handoff" and "Texto #tag" in text and "2026-10-27 05:00" in text


class FakePage:
    def __init__(self, broken=None):
        self.log, self.broken = [], broken
        self.keyboard = self

    def goto(self, url, **kw):
        self.log.append(("goto", url))

    def locator(self, sel):
        page = self

        class L:
            first = None

            def _do(self, kind, *a):
                if sel == page.broken:
                    raise TimeoutError(f"Timeout waiting for {sel}\nmore")
                page.log.append((kind, sel, *a))

            def set_input_files(self, f, timeout):
                self._do("upload", f)

            def click(self, timeout):
                self._do("click")

            def wait_for(self, state, timeout):
                self._do("wait_for")
        loc = L()
        loc.first = loc
        return loc

    def wait_for_timeout(self, ms):
        pass

    def press(self, key):
        self.log.append(("press", key))

    def insert_text(self, text):
        self.log.append(("type", text))


def test_browser_steps_render_text_and_skip_optional(tmp_path):
    steps = [{"do": "goto", "url": "u"}, {"do": "upload", "selector": "input"},
             {"do": "click", "selector": "maybe", "optional": True},
             {"do": "fill", "selector": "box", "text": "{caption}"}]
    page = FakePage(broken="maybe")
    browser.run_steps(page, steps, job(tmp_path, "tiktok", at(2026, 10, 27, 5)))
    assert ("type", "Texto #tag") in page.log and not any(e[1:2] == ("maybe",) for e in page.log)
    with pytest.raises(PublisherError, match=r"step 2 \(click must\): Timeout waiting for must$"):
        browser.run_steps(FakePage(broken="must"), [{"do": "goto", "url": "u"}, {"do": "click", "selector": "must"}],
                          job(tmp_path, "tiktok", at(2026, 10, 27, 5)))


def test_build_rejects_unknown_backend(settings):
    with pytest.raises(ValueError, match="unknown backend"):
        build("myspace_api", "tiktok", settings)
