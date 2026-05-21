"""Unit tests for the pure duration / age formatters in core.duration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ansible_aom.core.duration import format_age, format_duration_compact


def test_format_duration_seconds() -> None:
    assert format_duration_compact(0) == "0s"
    assert format_duration_compact(1) == "1s"
    assert format_duration_compact(42.4) == "42s"


def test_format_duration_minutes_pads_seconds() -> None:
    assert format_duration_compact(60) == "1m00s"
    assert format_duration_compact(83) == "1m23s"
    assert format_duration_compact(3599) == "59m59s"


def test_format_duration_hours_pads_minutes() -> None:
    assert format_duration_compact(3600) == "1h00m"
    assert format_duration_compact(3725) == "1h02m"
    assert format_duration_compact(99 * 3600 + 59 * 60) == "99h59m"


def test_format_age_seconds() -> None:
    now = datetime.now(timezone.utc)
    assert format_age(now) == "0s ago"
    assert format_age(now - timedelta(seconds=42)) == "42s ago"


def test_format_age_minutes() -> None:
    now = datetime.now(timezone.utc)
    assert format_age(now - timedelta(minutes=1)) == "1m ago"
    assert format_age(now - timedelta(minutes=30)) == "30m ago"


def test_format_age_hours() -> None:
    now = datetime.now(timezone.utc)
    assert format_age(now - timedelta(hours=2)) == "2h ago"
    assert format_age(now - timedelta(hours=23)) == "23h ago"


def test_format_age_days() -> None:
    now = datetime.now(timezone.utc)
    assert format_age(now - timedelta(days=3)) == "3d ago"
    assert format_age(now - timedelta(days=30)) == "30d ago"
