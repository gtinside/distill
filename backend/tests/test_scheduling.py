from datetime import datetime, timezone
from distill.scheduling import user_is_due


def test_due_when_local_time_matches_delivery_time():
    # 11:00 UTC == 07:00 America/New_York (EDT, summer)
    now = datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00", tz_name="America/New_York") is True


def test_not_due_when_local_time_differs():
    now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00", tz_name="America/New_York") is False


def test_handles_seconds_suffix_in_delivery_time():
    now = datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00:00", tz_name="America/New_York") is True


def test_unknown_timezone_falls_back_to_utc():
    now = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00", tz_name="Not/AZone") is True


def test_empty_delivery_time_is_not_due():
    now = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="", tz_name="UTC") is False
