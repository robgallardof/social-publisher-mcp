from datetime import date, datetime, time

import pytest

from social_forge.domain import insights, platforms, post, schedule


def test_render_puts_title_into_caption_where_no_title_field():
    spec = post.PostSpec.from_dict({"title": "Hook", "caption": "Body", "hashtags": ["gato", "#humor"]})
    tiktok = post.render(spec, "tiktok")
    assert tiktok.title is None
    assert tiktok.caption == "Hook\n\nBody\n\n#gato #humor"
    yt = post.render(spec, "youtube")
    assert yt.title == "Hook" and yt.caption == "Body\n\n#gato #humor" and yt.tags == ("gato", "humor")


def test_render_does_not_duplicate_hashtags_already_in_text():
    spec = post.PostSpec.from_dict({"caption": "Mira esto #gato", "hashtags": ["gato", "fyp"]})
    assert post.render(spec, "instagram").caption == "Mira esto #gato\n\n#fyp"


def test_overrides_win_per_platform():
    spec = post.PostSpec.from_dict({"caption": "A", "hashtags": ["x"], "title": "T",
                                    "overrides": {"tiktok": {"caption": "B", "hashtags": []}}})
    assert post.render(spec, "tiktok").caption == "T\n\nB"


def test_validate_limits():
    long = post.Copy("youtube", "x", title="t" * 101)
    assert "title 101 chars > 100" in post.validate(long)
    assert "missing title" in post.validate(post.Copy("youtube", "x"))
    many = post.Copy("tiktok", " ".join(f"#t{i}" for i in range(6)))
    assert "6 hashtags > 5" in post.validate(many)
    assert post.validate(post.Copy("tiktok", "ok #a")) == []


def test_post_spec_rejects_unknown_keys_and_platforms():
    with pytest.raises(ValueError, match="unknown keys"):
        post.PostSpec.from_dict({"captoin": "typo"})
    with pytest.raises(ValueError, match="unknown platform"):
        post.PostSpec.from_dict({"caption": "x", "platforms": ["myspace"]})


def test_folder_names():
    assert schedule.parse_day("2026-10-27") == date(2026, 10, 27)
    assert schedule.parse_day("2026-13-01") is None
    week = schedule.parse_week("2026-W44")
    assert week[0] == date(2026, 10, 26) and week[-1] == date(2026, 11, 1)
    assert schedule.week_name(date(2026, 10, 24)) == "2026-W43"


def test_distribute_even_and_capped():
    days = schedule.parse_week("2026-W44")
    even = schedule.distribute([f"v{i}.mp4" for i in range(10)], days)
    assert [len(v) for v in even.values()] == [2, 2, 2, 1, 1, 1, 1]
    capped = schedule.distribute([f"v{i}.mp4" for i in range(10)], days[:3], per_day=3)
    assert sum(map(len, capped.values())) == 9
    weekdays = schedule.distribute(["a", "b"], days, skip_weekdays=(5, 6))
    assert set(weekdays) == set(days[:5])


def test_slot_is_aware_and_staggers():
    s = schedule.slot(date(2026, 10, 27), time(5), "America/Mexico_City", index=2, stagger_minutes=10)
    assert s.hour == 5 and s.minute == 20 and s.utcoffset().total_seconds() == -6 * 3600


def test_platform_table_lists_all():
    table = platforms.markdown_table()
    assert all(p.name in table for p in platforms.PLATFORMS.values())


def test_insights_uses_latest_snapshot_and_ranks():
    d = datetime(2026, 10, 26, 5)
    rows = [insights.Metric("tiktok", "a", d, 100, 10), insights.Metric("tiktok", "a", d, 1000, 100, shares=50),
            insights.Metric("tiktok", "b", d.replace(day=27), 50, 1)]
    out = insights.summarize(rows)
    assert out["platforms"]["tiktok"]["views_total"] == 1050
    assert out["top"][0]["video"] == "a"
    assert out["platforms"]["tiktok"]["best_weekdays"][0].startswith("Mon")
    assert "anecdotal" in out["note"]
