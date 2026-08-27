from datetime import datetime, timezone

from workers.campaign_runner import (
    pace_seconds,
    local_window,
)


def campaign(**overrides):
    data = {
        "timezone": "America/New_York",
        "calling_days": [
            "mon",
            "tue",
            "wed",
            "thu",
            "fri",
        ],
        "calling_hours_start": "09:00",
        "calling_hours_end": "17:00",
        "calls_per_hour": 100,
        "calls_per_day": 100,
    }

    data.update(overrides)
    return data


def test_100_calls_hour_equals_36_seconds():
    assert pace_seconds(100) == 36.0


def test_missing_timezone_fails_closed():
    ok, reason, _ = local_window(
        campaign(timezone=""),
        datetime(
            2026,
            8,
            27,
            15,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert ok is False
    assert reason == "timezone_missing"


def test_invalid_timezone_fails_closed():
    ok, reason, _ = local_window(
        campaign(timezone="Bad/Timezone"),
        datetime(
            2026,
            8,
            27,
            15,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert ok is False
    assert reason == "timezone_invalid"


def test_georgia_uses_new_york_time():
    # 15:00 UTC = 11:00 EDT
    ok, reason, local = local_window(
        campaign(),
        datetime(
            2026,
            8,
            27,
            15,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert ok is True
    assert reason == "ok"
    assert local.hour == 11


def test_after_hours_is_blocked():
    # 23:00 UTC = 19:00 EDT
    ok, reason, _ = local_window(
        campaign(),
        datetime(
            2026,
            8,
            27,
            23,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert ok is False
    assert reason == "outside_calling_hours"
