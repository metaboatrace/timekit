# metaboatrace.timekit

metaboatrace パイプラインで共有する時刻ヘルパ。組織横断の時刻規約
（[handbook の時刻の取り扱い標準](https://github.com/metaboatrace/handbook/blob/main/engineering/timezone.md)）を
コードで守るための最小ユーティリティを提供する。

## 規約 (要約)

- **instant**（`created_at` / `decided_at` / `placed_at` など「いつ起きたか」）は常に
  timezone-aware。**保存・交換は UTC**、**表示は JST** に変換する。
- **暦日**（`race_id` の `YYYYMMDD`・「今日」など）は **JST 暦** で解釈する。

各リポが独自に `now()` や tz 定数を実装するとドリフトの温床になるため、ここに集約する。

## API

| 名前 | 用途 |
| ---- | ---- |
| `JST` | 日本標準時（固定 +09:00） |
| `UTC` | `datetime.UTC` の再エクスポート |
| `now_utc()` | 現在時刻を aware UTC で（instant 生成の正準） |
| `now_jst()` | 現在時刻を aware JST で（JST 壁時計が要るとき） |
| `today_jst()` | JST 暦の「今日」（`date`） |
| `ensure_aware(dt)` | naive を UTC とみなして aware 化 |
| `to_utc(dt)` | aware UTC へ正規化（保存・wire 用） |
| `to_jst(dt)` | aware JST へ変換（表示の直前） |

## インストール

```
metaboatrace.timekit @ git+https://github.com/metaboatrace/timekit.git@v0.1.1
```

## 開発

```sh
uv sync
uv run ruff check metaboatrace tests
uv run mypy metaboatrace
uv run pytest
```
