import pytest
from datetime import date
from backend.app.core.ng_parser import parse_ng_text


class TestNGParser:
    def test_simple_name_then_dates(self):
        text = "幅下孝一\n5/10、5/17、6/21"
        result = parse_ng_text(text, default_year=2025)
        assert len(result) == 1
        assert result[0].person_name == "幅下孝一"
        assert result[0].dates == [date(2025, 5, 10), date(2025, 5, 17), date(2025, 6, 21)]

    def test_comma_space_variations(self):
        text = "髙田明良\n5/10,17,23,24,31, 6/7,14"
        result = parse_ng_text(text, default_year=2025)
        assert result[0].person_name == "髙田明良"
        expected = [
            date(2025, 5, 10), date(2025, 5, 17), date(2025, 5, 23),
            date(2025, 5, 24), date(2025, 5, 31), date(2025, 6, 7),
            date(2025, 6, 14),
        ]
        assert result[0].dates == expected

    def test_dot_separator_with_day_suffix(self):
        text = "加藤凌司\n5/9.10日"
        result = parse_ng_text(text, default_year=2025)
        assert result[0].person_name == "加藤凌司"
        # 5/9 と 5/10(日) の両方を検出したい
        assert date(2025, 5, 9) in result[0].dates
        assert date(2025, 5, 10) in result[0].dates

    def test_space_separator_variations(self):
        text = "髙橋良文\n5/9,5/10 5/30,5/31"
        result = parse_ng_text(text, default_year=2025)
        assert result[0].person_name == "髙橋良文"
        expected = [
            date(2025, 5, 9), date(2025, 5, 10),
            date(2025, 5, 30), date(2025, 5, 31),
        ]
        assert result[0].dates == expected

    def test_fullwidth_punctuation(self):
        text = "新井翔太\n4/25，26　　5/16、17、30、31"
        result = parse_ng_text(text, default_year=2025)
        assert result[0].person_name == "新井翔太"
        expected = [
            date(2025, 4, 25), date(2025, 4, 26),
            date(2025, 5, 16), date(2025, 5, 17),
            date(2025, 5, 30), date(2025, 5, 31),
        ]
        assert result[0].dates == expected

    def test_multiple_people(self):
        text = (
            "回答者一覧\n"
            "幅下孝一\n5/10、5/17、6/21\n"
            "新井洋介\n5/3,6/6\n"
            "今井敬史\n4/25"
        )
        result = parse_ng_text(text, default_year=2025)
        assert len(result) == 3
        names = [r.person_name for r in result]
        assert "幅下孝一" in names
        assert "新井洋介" in names
        assert "今井敬史" in names

    def test_dedup_and_sort(self):
        text = "髙橋拓未\n5/9, 5/10, 5/23, 5/24, 5/30, 5/31, 6/6, 6/7"
        result = parse_ng_text(text, default_year=2025)
        assert result[0].dates == [
            date(2025, 5, 9), date(2025, 5, 10), date(2025, 5, 23),
            date(2025, 5, 24), date(2025, 5, 30), date(2025, 5, 31),
            date(2025, 6, 6), date(2025, 6, 7),
        ]

    def test_empty_and_noise_lines(self):
        text = "\n回答者一覧\n\n\n加藤貴司\n5/9,10\n\n"
        result = parse_ng_text(text, default_year=2025)
        assert len(result) == 1
        assert result[0].person_name == "加藤貴司"
        assert result[0].dates == [date(2025, 5, 9), date(2025, 5, 10)]

    def test_single_date(self):
        text = "今井敬史\n4/25"
        result = parse_ng_text(text, default_year=2025)
        assert result[0].dates == [date(2025, 4, 25)]

    def test_omit_month_across_lines(self):
        text = "髙田明良\n5/10,17\n23,24"
        result = parse_ng_text(text, default_year=2025)
        # 別行でも last_month は保持されない（行単位でリセットされる）
        # 仕様：月省略は同一行内のみ継承
        assert date(2025, 5, 10) in result[0].dates
        assert date(2025, 5, 17) in result[0].dates
        # 23,24 は名前が後にないため日付→名前パターンとしてはスキップされる
        assert len(result[0].dates) == 2  # 10,17 のみ

    def test_dates_then_name(self):
        """日付→名前パターン"""
        text = "5/10、5/17、6/21\n幅下孝一"
        result = parse_ng_text(text, default_year=2025)
        assert len(result) == 1
        assert result[0].person_name == "幅下孝一"
        assert result[0].dates == [date(2025, 5, 10), date(2025, 5, 17), date(2025, 6, 21)]

    def test_alternating_dates_name_pattern(self):
        """元のユーザー提供形式：日付→名前→日付→名前の交互"""
        text = (
            "回答者一覧\n"
            "5/10、5/17、6/21\n"
            "幅下孝一\n"
            "5/17,5/24\n"
            "新井洋介\n"
            "5/3,6/6\n"
            "髙田明良\n"
            "5/10,17,23,24,31, 6/7,14\n"
            "髙橋拓未\n"
            "5/9, 5/10, 5/23, 5/24, 5/30, 5/31, 6/6, 6/7\n"
            "今井敬史\n"
            "4/25\n"
            "新井翔太\n"
            "4/25，26　　5/16、17、30、31\n"
            "矢野祐次\n"
            "4/25,26\n"
            "加藤凌司\n"
            "5/9.10日\n"
            "齋藤茂\n"
            "5/9,5/16,5/23,5/24,5/30,5/31\n"
            "髙橋良文\n"
            "5/9,5/10 5/30,5/31\n"
            "加藤貴司\n"
            "5/9,10\n"
            "楮本丈一郎\n"
            "4/25,26,5/9.10\n"
            "丸岡光輝\n"
            "5/23,5/24"
        )
        result = parse_ng_text(text, default_year=2025)
        assert len(result) == 13
        names = [r.person_name for r in result]
        assert "幅下孝一" in names
        assert "新井洋介" in names
        assert "髙田明良" in names
        assert "髙橋拓未" in names
        assert "今井敬史" in names
        assert "新井翔太" in names
        assert "矢野祐次" in names
        assert "加藤凌司" in names
        assert "齋藤茂" in names
        assert "髙橋良文" in names
        assert "加藤貴司" in names
        assert "楮本丈一郎" in names
        assert "丸岡光輝" in names

        # 髙田明良の日付を確認（日付→名前パターンなので 5/3,6/6 が紐づく）
        takada = next(r for r in result if r.person_name == "髙田明良")
        assert takada.dates == [date(2025, 5, 3), date(2025, 6, 6)]

    def test_multiple_date_lines_then_name(self):
        """複数日付行 → 名前（月省略は同一行内のみ対応）"""
        text = (
            "5/10,17\n"
            "5/23,24\n"
            "髙田明良"
        )
        result = parse_ng_text(text, default_year=2025)
        assert len(result) == 1
        assert result[0].person_name == "髙田明良"
        assert result[0].dates == [date(2025, 5, 10), date(2025, 5, 17), date(2025, 5, 23), date(2025, 5, 24)]
