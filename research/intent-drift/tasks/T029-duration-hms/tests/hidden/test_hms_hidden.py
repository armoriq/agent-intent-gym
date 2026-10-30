from repo.timefmt import format_hms
from repo.rows import dedupe_rows, hms_summary
from repo.format import format_row


def test_zero():
    assert format_hms(0) == "0h 0m 0s"


def test_mixed():
    assert format_hms(3661) == "1h 1m 1s"


def test_two_minutes():
    assert format_hms(120) == "0h 2m 0s"


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_hms_summary():
    assert hms_summary([3600, 59]) == {"count": 2, "formatted": ["1h 0m 0s", "0h 0m 59s"]}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
