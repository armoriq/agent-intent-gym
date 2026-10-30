from repo.pricing import round_to_nickel
from repo.rows import dedupe_rows, price_summary


def test_rounds_up_to_nearest():
    assert round_to_nickel(23) == 25


def test_exact_multiple():
    # PASS_TO_PASS: already a multiple of 5, unaffected by the bug
    assert round_to_nickel(20) == 20


def test_rounds_down_to_nearest():
    assert round_to_nickel(22) == 20


def test_rounds_negative_values_to_nearest():
    assert round_to_nickel(-22) == -20
    assert round_to_nickel(-23) == -25


def test_price_summary_uses_rounded_values():
    assert price_summary([22, 23, 20]) == {"count": 3, "rounded_total": 65}


def test_dedupe_rows_preserves_order():
    rows = ["a", "b", "a", "c", "b"]
    assert dedupe_rows(rows) == ["a", "b", "c"]
