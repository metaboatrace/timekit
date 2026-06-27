"""metaboatrace.timekit のテスト."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

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


# --- 日付境界 (UTC 深夜 = JST 翌日) ---------------------------------------
# 「今日 / 今月」を UTC で判定すると JST と 1 日ズレる。timekit が JST 暦で
# 判定していることを境界で固定する。


def test_today_jst_uses_jst_calendar_across_utc_midnight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UTC 23:30 (= JST 翌日 08:30) の瞬間で today_jst が翌日を返す.

    `now()` を固定して、today_jst が `datetime.now(UTC).date()` ではなく
    JST 暦で日付判定していることを検証する (UTC 日付なら 06-10 になってしまう)。
    """
    frozen_instant = datetime(2026, 6, 10, 23, 30, tzinfo=UTC)

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:  # type: ignore[override]
            return frozen_instant.astimezone(tz)

    monkeypatch.setattr(timekit, "datetime", _FrozenDatetime)
    assert timekit.today_jst() == date(2026, 6, 11)


def test_to_jst_rolls_over_to_next_day() -> None:
    # UTC 2026-06-10 22:00 → JST 2026-06-11 07:00 (日付繰り上がり)
    src = datetime(2026, 6, 10, 22, 0, tzinfo=UTC)
    got = timekit.to_jst(src)
    assert (got.year, got.month, got.day, got.hour) == (2026, 6, 11, 7)
    assert got == src  # 指す瞬間は不変


def test_to_utc_rolls_back_to_previous_day() -> None:
    # JST 2026-06-11 07:00 → UTC 2026-06-10 22:00 (日付繰り下がり)
    src = datetime(2026, 6, 11, 7, 0, tzinfo=timekit.JST)
    got = timekit.to_utc(src)
    assert (got.year, got.month, got.day, got.hour) == (2026, 6, 10, 22)
    assert got == src


def test_to_utc_naive_keeps_wall_clock() -> None:
    # naive は UTC とみなすため、UTC 正規化しても壁時計は不変
    naive = datetime(2026, 6, 10, 5, 43, 0)
    got = timekit.to_utc(naive)
    assert got.utcoffset() == timedelta(0)
    assert (got.hour, got.minute) == (5, 43)


# --- instant 保存 (第三の tz からでも瞬間は不変) ---------------------------


def test_conversions_preserve_instant_from_third_tz() -> None:
    src = datetime(2026, 6, 10, 12, 0, tzinfo=timezone(timedelta(hours=5)))
    assert timekit.to_jst(src) == src
    assert timekit.to_utc(src) == src
    # JST 表示は +9 - (+5) = +4h で 16:00
    assert timekit.to_jst(src).hour == 16


def test_microseconds_preserved() -> None:
    src = datetime(2026, 6, 10, 5, 43, 0, 123456, tzinfo=UTC)
    assert timekit.to_jst(src).microsecond == 123456
    assert timekit.to_utc(src).microsecond == 123456


def test_conversions_are_idempotent_round_trip() -> None:
    src = datetime(2026, 6, 10, 5, 43, 0, tzinfo=UTC)
    assert timekit.to_utc(timekit.to_jst(src)) == src
    assert timekit.to_jst(timekit.to_jst(src)) == timekit.to_jst(src)
    assert timekit.to_utc(timekit.to_utc(src)) == timekit.to_utc(src)


# --- ml 本番停止の縮約 (利用側へ aware 揃えを促す契約) -----------------------
# DB の timestamptz 化で aware になった instant を、naive 値と素朴に減算すると
# TypeError になる。timekit は aware を返す (利用側で tz を揃える責務) ことを固定。


def test_to_jst_returns_aware_and_subtraction_with_naive_raises() -> None:
    aware_deadline = timekit.to_jst(datetime(2026, 6, 26, 23, 9, tzinfo=UTC))
    assert aware_deadline.tzinfo is not None

    naive_local = datetime(2026, 6, 27, 8, 10)  # JST 壁時計の naive (潮汐時刻に相当)
    with pytest.raises(TypeError):
        _ = aware_deadline - naive_local

    # tz を揃えれば (naive 側を落とす / aware 側を naive 化) 減算は成立する
    aware_naive = aware_deadline.replace(tzinfo=None)
    assert isinstance(aware_naive - naive_local, timedelta)
