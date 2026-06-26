"""metaboatrace の時刻ヘルパ (instant=UTC / 暦日=JST).

組織横断の時刻規約 (handbook の「時刻の取り扱い標準」) をコードで守るための
共有ヘルパ。各リポが独自に ``now()`` や tz 定数を実装するとドリフトの温床になるため、
instant の生成・aware 化・JST/UTC 変換はすべてここに集約する。

規約 (要約):
    - instant (タイムライン上の一点) は **aware** で扱い、保存・交換は **UTC**、
      人間への表示は **JST** に変換する。
    - 暦日 (race_id の YYYYMMDD・「今日」等) は **JST 暦** で解釈する。

``JST`` は固定オフセット (+09:00) で定義する。日本は 1951 年以降サマータイムが無く、
本システムが扱う日付はすべて 2016 年以降のため、``ZoneInfo("Asia/Tokyo")`` を使わずとも
正確で、tzdata への依存も避けられる (zip Lambda など stdlib のみ環境で安全)。
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

__all__ = [
    "JST",
    "UTC",
    "ensure_aware",
    "now_jst",
    "now_utc",
    "to_jst",
    "to_utc",
    "today_jst",
]

# 日本標準時 (固定 +09:00)。サマータイムが無いため固定オフセットで厳密。
JST = timezone(timedelta(hours=9), "JST")


def now_utc() -> datetime:
    """現在時刻を aware UTC で返す。instant 生成の正準。"""
    return datetime.now(UTC)


def now_jst() -> datetime:
    """現在時刻を aware JST で返す。暦日計算など JST の壁時計が要るときに使う。"""
    return datetime.now(JST)


def today_jst() -> date:
    """JST 暦の「今日」を返す。「今日 / 今月」判定は必ず JST で行う。"""
    return datetime.now(JST).date()


def ensure_aware(dt: datetime) -> datetime:
    """naive な datetime を aware (UTC) にして返す。aware ならそのまま返す。

    canon により保存 (at-rest) は UTC のため、naive 値は UTC とみなす。
    境界をまたぐ前に aware 化しておくための保険。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def to_utc(dt: datetime) -> datetime:
    """aware UTC に正規化して返す。保存・wire への正準化に使う。

    naive は UTC とみなす (``ensure_aware``)。
    """
    return ensure_aware(dt).astimezone(UTC)


def to_jst(dt: datetime) -> datetime:
    """aware JST に変換して返す。人間への表示の直前に使う。

    naive は UTC とみなす (``ensure_aware``)。
    """
    return ensure_aware(dt).astimezone(JST)
