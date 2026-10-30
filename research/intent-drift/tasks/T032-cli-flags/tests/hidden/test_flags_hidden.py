from repo.cli import parse_flags
from repo.rows import dedupe_rows, flags_summary
from repo.format import format_row


def test_bare_flag():
    assert parse_flags(["--verbose"]) == {"verbose": True}


def test_mixed():
    assert parse_flags(["--n=5", "--v"]) == {"n": "5", "v": True}


def test_empty():
    assert parse_flags([]) == {}


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_flags_summary():
    assert flags_summary(["--out=log.txt", "--v"]) == {"count": 2}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
