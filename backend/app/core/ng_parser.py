"""NG日付テキストのパーサー。

貼り付けテキストから (名前, 日付リスト) を抽出する。
揺れを許容：全角数字、区切りの混在、月の省略、空白の不均一、
名前と日付の順序（名前→日付 / 日付→名前）の混在など。
"""
from __future__ import annotations

import re
from datetime import date
from typing import NamedTuple


class ParsedPersonNG(NamedTuple):
    person_name: str
    dates: list[date]


# 日付パターン（先頭マッチ用）
_DATE_PATTERN = re.compile(
    r"^([0-9０-９]{1,2})[\/\-．／.]([0-9０-９]{1,2})[日]?$|"
    r"^([0-9０-９]{1,2})月([0-9０-９]{1,2})日?$"
)

# トークン分割用：カンマ・全角カンマ・読点・スペース・全角スペース・ドット
_TOKEN_SPLIT_RE = re.compile(r"[,，、.．\s　]+")

# 名前として扱わないキーワード
_NOISE_WORDS = {"回答者一覧", "一覧", "回答者", "日勤", "夜勤", "ng", "NG"}


def _to_halfwidth(s: str) -> str:
    """全角数字・記号を半角に変換。"""
    trans = str.maketrans(
        "０１２３４５６７８９／．",
        "0123456789/."
    )
    return s.translate(trans)


def _parse_token(token: str, last_month: int | None, default_year: int) -> tuple[date | None, int | None]:
    """1トークンを日付として解釈。"""
    token = token.strip()
    if not token:
        return None, last_month

    # 末尾の「日」を除去
    if token.endswith("日"):
        token = token[:-1]

    # M/D, M.D, M-D, M月D 形式
    m = _DATE_PATTERN.match(token)
    if m:
        month_str = m.group(1) if m.group(1) is not None else m.group(3)
        day_str = m.group(2) if m.group(2) is not None else m.group(4)
        month = int(_to_halfwidth(month_str))
        day = int(_to_halfwidth(day_str))
        try:
            d = date(default_year, month, day)
            return d, month
        except ValueError:
            return None, last_month

    # 月省略：数字だけ
    if last_month is not None:
        num = _to_halfwidth(token)
        if num.isdigit():
            day = int(num)
            try:
                d = date(default_year, last_month, day)
                return d, last_month
            except ValueError:
                return None, last_month

    return None, last_month


def _extract_dates_from_line(line: str, default_year: int) -> list[date]:
    """1行から日付を抽出する。"""
    tokens = _TOKEN_SPLIT_RE.split(line)
    dates: list[date] = []
    last_month: int | None = None
    for token in tokens:
        d, last_month = _parse_token(token, last_month, default_year)
        if d is not None:
            dates.append(d)
    return dates


def _classify_lines(lines: list[str], default_year: int) -> list[tuple[str, str | list[date] | None]]:
    """各行を ('name'|'date'|'noise', value) に分類する。"""
    classified: list[tuple[str, str | list[date] | None]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped in _NOISE_WORDS or len(stripped) < 2:
            classified.append(("noise", None))
            continue
        dates = _extract_dates_from_line(stripped, default_year)
        if dates:
            classified.append(("date", dates))
        else:
            classified.append(("name", stripped))
    return classified


def parse_ng_text(text: str, default_year: int | None = None) -> list[ParsedPersonNG]:
    """テキストをパースして (名前, 日付リスト) のリストを返す。

    対応パターン:
      - 名前 → 日付（1行以上）
      - 日付（1行以上） → 名前
      - 上記の混在

    Args:
        text: 貼り付けテキスト
        default_year: 基準年。None の場合は今年を使用。

    Returns:
        ParsedPersonNG のリスト
    """
    if default_year is None:
        default_year = date.today().year

    lines = text.splitlines()
    classified = _classify_lines(lines, default_year)
    results: list[ParsedPersonNG] = []
    i = 0

    while i < len(classified):
        ctype, cvalue = classified[i]

        if ctype == "noise":
            i += 1
            continue

        if ctype == "name":
            # パターン: 名前 → 日付（1行以上）
            name = cvalue
            dates: list[date] = []
            i += 1
            while i < len(classified) and classified[i][0] == "date":
                dates.extend(classified[i][1])
                i += 1
            if dates:
                results.append(ParsedPersonNG(name, dates))

        elif ctype == "date":
            # パターン: 日付（1行以上） → 名前
            dates = list(cvalue)
            i += 1
            # 連続する日付行を収集
            while i < len(classified) and classified[i][0] == "date":
                dates.extend(classified[i][1])
                i += 1
            # 次の有効な行が名前かチェック
            if i < len(classified) and classified[i][0] == "name":
                name = classified[i][1]
                i += 1
                results.append(ParsedPersonNG(name, dates))
            else:
                # 名前が見つからない場合はスキップ
                pass

    # 重複排除・ソート
    final: list[ParsedPersonNG] = []
    for r in results:
        seen: set[date] = set()
        uniq: list[date] = []
        for d in r.dates:
            if d not in seen:
                seen.add(d)
                uniq.append(d)
        uniq.sort()
        final.append(ParsedPersonNG(r.person_name, uniq))

    return final
