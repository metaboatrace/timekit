"""metaboatrace.timekit のテスト."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from metaboatrace import timekit


def test_jst_is_fixed_plus_nine() -> None:
    assert timekit.JST.utcoffset(None) == timedelta(hours=9)


def test_now_utc_is_aware_utc() -> None:
    now = timekit.now_utc()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_now_jst_is_aware_jst() -> None:
    now = timekit.now_jst()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(hours=9)


def test_today_jst_returns_date() -> None:
    assert isinstance(timekit.today_jst(), date)


def test_to_jst_converts_utc_to_jst() -> None:
    # UTC 05:43 → JST 14:43 (同一の瞬間)
    src = datetime(2026, 6, 10, 5, 43, 0, tzinfo=UTC)
    got = timekit.to_jst(src)
    assert got.utcoffset() == timedelta(hours=9)
    assert (got.hour, got.minute) == (14, 43)
    assert got == src  # 指す瞬間は不変


def test_to_utc_converts_jst_to_utc() -> None:
    src = datetime(2026, 6, 10, 14, 43, 0, tzinfo=timekit.JST)
    got = timekit.to_utc(src)
    assert got.utcoffset() == timedelta(0)
    assert (got.hour, got.minute) == (5, 43)
    assert got == src


def test_naive_is_treated_as_utc() -> None:
    naive = datetime(2026, 6, 10, 5, 43, 0)
    assert timekit.ensure_aware(naive).utcoffset() == timedelta(0)
    # naive を UTC とみなして JST へ → 14:43
    assert timekit.to_jst(naive).hour == 14


def test_ensure_aware_keeps_existing_tz() -> None:
    aware = datetime(2026, 6, 10, 14, 43, 0, tzinfo=timekit.JST)
    assert timekit.ensure_aware(aware) is aware
