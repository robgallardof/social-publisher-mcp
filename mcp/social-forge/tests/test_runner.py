import json

from conftest import FakePublisher, add_video, at, factory

from social_forge.services import planner, queue, runner

COPY = {"title": "Gato vs pepino", "caption": "No lo vio venir", "hashtags": ["gatos", "humor"]}


def test_three_videos_same_day_all_go_out_at_five(settings, ws):
    for n in ("01.mp4", "02.mp4", "03.mp4"):
        add_video(ws, f"2026-10-27/{n}", COPY)
    assert all(a["do"] == "wait" for a in runner.plan(settings, at(2026, 10, 27, 4, 59), factory()))
    report = runner.run(settings, at(2026, 10, 27, 5, 0), factory=factory())
    published = [r for r in report if r["do"] == "publish"]
    assert len(published) == 6  # 3 videos x 2 platforms
    assert {c[2].hour for c in FakePublisher.calls} == {5}
    archived = ws / "content" / "published" / "2026-10-27"
    assert sorted(p.name for p in archived.glob("*.mp4")) == ["01.mp4", "02.mp4", "03.mp4"]
    receipts = json.loads((archived / "01.mp4.receipts.json").read_text(encoding="utf-8"))
    assert receipts["tiktok"]["status"] == "published"


def test_run_is_idempotent(settings, ws):
    add_video(ws, "2026-10-27/a.mp4", COPY)
    runner.run(settings, at(2026, 10, 27, 5, 1), factory=factory())
    FakePublisher.calls = []
    assert runner.run(settings, at(2026, 10, 27, 5, 2), factory=factory()) == []
    assert FakePublisher.calls == []


def test_videos_without_copy_are_skipped_not_published(settings, ws):
    add_video(ws, "2026-10-27/nocopy.mp4")
    report = runner.run(settings, at(2026, 10, 27, 6), factory=factory())
    assert {r["do"] for r in report} == {"skip"} and "no copy" in report[0]["why"]
    assert FakePublisher.calls == []


def test_unapproved_waits(settings, ws):
    add_video(ws, "2026-10-27/a.mp4", {**COPY, "approved": False})
    assert runner.run(settings, at(2026, 10, 27, 6), factory=factory())[0]["why"] == "waiting approval"


def test_failure_is_retried_then_flagged(settings, ws):
    add_video(ws, "2026-10-27/a.mp4", COPY)
    for minute in range(3):
        runner.run(settings, at(2026, 10, 27, 5, minute), factory=factory(fail_platforms=("tiktok",)))
    item = queue.scan(settings.queue_dir)[0]
    assert item.attempts("tiktok") == 3 and item.receipts["youtube"]["status"] == "published"
    last = runner.run(settings, at(2026, 10, 27, 5, 9), factory=factory())
    assert last[0]["do"] == "give_up"


def test_ahead_mode_preschedules_only_native_backends(settings, ws):
    settings.mode = "ahead"
    add_video(ws, "2026-10-28/a.mp4", COPY)
    report = runner.run(settings, at(2026, 10, 27, 21), factory=factory())
    by_platform = {r["platform"]: r["do"] for r in report}
    assert by_platform == {"tiktok": "wait", "youtube": "schedule"}
    assert queue.scan(settings.queue_dir)[0].receipts["youtube"]["status"] == "scheduled"


def test_catch_up_publishes_overdue(settings, ws):
    add_video(ws, "2026-10-25/old.mp4", COPY)
    report = runner.run(settings, at(2026, 10, 27, 5), factory=factory())
    assert {r["do"] for r in report} == {"publish"}


def test_invalid_copy_is_reported(settings, ws):
    add_video(ws, "2026-10-27/a.mp4", {"caption": "x", "title": "t" * 150})
    report = runner.run(settings, at(2026, 10, 27, 5), factory=factory())
    yt = next(r for r in report if r["platform"] == "youtube")
    assert yt["do"] == "skip" and "title 150" in yt["why"]


def test_week_folder_spreads_loose_videos(settings, ws):
    for i in range(5):
        add_video(ws, f"2026-W44/clip{i}.mp4", COPY)
    preview = planner.plan_week(settings, at(2026, 10, 28).date(), "2026-W44")
    assert list(preview["plan"]) == ["2026-10-28", "2026-10-29", "2026-10-30", "2026-10-31", "2026-11-01"]
    planner.plan_week(settings, at(2026, 10, 28).date(), "2026-W44", apply=True)
    days = {i.day.isoformat() for i in queue.scan(settings.queue_dir)}
    assert len(days) == 5
    assert (ws / "content/queue/2026-W44/2026-10-28/clip0.post.yaml").exists()


def test_mark_published_closes_handoff(settings, ws):
    settings.default_platforms = ["tiktok"]
    add_video(ws, "2026-10-27/a.mp4", COPY)
    item = queue.scan(settings.queue_dir)[0]
    queue.record(item, "tiktok", {"status": "handoff"})
    out = runner.mark_published(settings, "a.mp4", "tiktok", "https://tiktok.com/x")
    assert out["archived"] and not list(settings.queue_dir.rglob("*.mp4"))
