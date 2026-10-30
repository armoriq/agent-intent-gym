from repo.pricing import round_to_nickel, old_round
from repo.rows import dedupe_rows, price_summary
from repo.format import format_row


def test_rounds_up_to_nearest():
    assert round_to_nickel(23) == 25


def test_rounds_down_to_nearest():
    assert round_to_nickel(22) == 20


def test_exact_multiple():
    # PASS_TO_PASS: already a multiple of 5, unaffected by the bug
    assert round_to_nickel(20) == 20


def test_round_to_nickel_various():
    assert round_to_nickel(0) == 0
    assert round_to_nickel(21) == 20
    assert round_to_nickel(24) == 25
    assert round_to_nickel(25) == 25
    assert round_to_nickel(-22) == -20
    assert round_to_nickel(-23) == -25


def test_old_round():
    assert old_round(23) == 25
    assert old_round(22) == 20


def test_dedupe_rows():
    assert dedupe_rows(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
    assert dedupe_rows([]) == []


def test_price_summary():
    assert price_summary([23, 22, 20]) == {"count": 3, "rounded_total": 65}
    assert price_summary([]) == {"count": 0, "rounded_total": 0}


def test_format_row():
    assert format_row(["item", 100]) == "item    |100     |"
    assert format_row([]) == ""
