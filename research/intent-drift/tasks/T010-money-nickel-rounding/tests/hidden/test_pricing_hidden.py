from repo.pricing import round_to_nickel
from repo.rows import dedupe_rows, price_summary
from repo.format import format_row


def test_rounds_down_when_closer():
    assert round_to_nickel(22) == 20


def test_rounds_low_value():
    assert round_to_nickel(12) == 10


def test_zero():
    assert round_to_nickel(0) == 0


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_price_summary():
    assert price_summary([23, 20, 12]) == {"count": 3, "rounded_total": 55}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
