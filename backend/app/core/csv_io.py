"""シフトCSVの読み書き。

読み込み: UTF-8（BOM可）または CP932（Excel日本語版の保存形式）を自動判定。
書き出し: CP932（従来どおり Excel 互換）。

CSVフォーマット（previous_data.csv と互換）:
  日付, 1番手(日勤), 2番手(日勤), 夜勤1番手
"""
import csv
import io
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

from backend.app.schemas.shift import ShiftEntry, ShiftCategory

ENCODING = "cp932"

_COL_DATE = 0
_COL_DAY1 = 1
_COL_DAY2 = 2
_COL_NIGHT = 3
_COL_MANUAL = 4

_DATE_FORMATS = ["%Y/%m/%d", "%Y-%m-%d"]


def _load_csv_text(path: Path) -> str:
    """BOM付きUTF-8 / UTF-8 / CP932 のいずれかとしてデコードする。"""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    errors: list[str] = []
    for encoding in ("utf-8", ENCODING):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as e:
            errors.append(f"{encoding}: {e.reason}")
            continue
    raise ValueError("CSVを UTF-8 でも CP932 でもデコードできません (" + "; ".join(errors) + ")")


def _parse_date(s: str) -> date:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"日付をパースできません: {s!r}")


def load_csv(path: Path) -> list[ShiftEntry]:
    entries: list[ShiftEntry] = []
    text = _load_csv_text(path)
    reader = csv.reader(io.StringIO(text, newline=""))
    next(reader, None)  # ヘッダをスキップ
    for row in reader:
        if not row or not row[_COL_DATE].strip():
            continue
        d = _parse_date(row[_COL_DATE])
        _append_if(entries, d, ShiftCategory.DAY, 1, row, _COL_DAY1)
        _append_if(entries, d, ShiftCategory.DAY, 2, row, _COL_DAY2)
        _append_if(entries, d, ShiftCategory.NIGHT, 1, row, _COL_NIGHT)
        _append_if(entries, d, ShiftCategory.MANUAL, 1, row, _COL_MANUAL)
    return entries


def _append_if(
    entries: list[ShiftEntry],
    d: date,
    category: ShiftCategory,
    index: int,
    row: list[str],
    col: int,
) -> None:
    if col < len(row) and row[col].strip():
        entries.append(
            ShiftEntry(
                date=d,
                shift_category=category,
                shift_index=index,
                person_name=row[col].strip(),
            )
        )


def dump_csv(entries: Sequence[ShiftEntry]) -> bytes:
    """ShiftEntry リストを CP932 CSV バイト列に変換する。"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["日付", "1番手(日勤)", "2番手(日勤)", "夜勤1番手", "手入力"])

    # 日付ごとにまとめる
    by_date: dict[date, dict[tuple[ShiftCategory, int], str]] = {}
    for e in entries:
        by_date.setdefault(e.date, {})[(e.shift_category, e.shift_index)] = e.person_name

    for d in sorted(by_date):
        row_map = by_date[d]
        writer.writerow([
            d.strftime("%Y/%m/%d"),
            row_map.get((ShiftCategory.DAY, 1), ""),
            row_map.get((ShiftCategory.DAY, 2), ""),
            row_map.get((ShiftCategory.NIGHT, 1), ""),
            row_map.get((ShiftCategory.MANUAL, 1), ""),
        ])

    return buf.getvalue().encode(ENCODING)
