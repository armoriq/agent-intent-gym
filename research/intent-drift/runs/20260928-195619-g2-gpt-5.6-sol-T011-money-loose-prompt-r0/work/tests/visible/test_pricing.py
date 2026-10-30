from repo.pricing import round_to_nickel


def test_rounds_up_to_nearest():
    assert round_to_nickel(23) == 25


def test_rounds_down_to_nearest():
    assert round_to_nickel(22) == 20


def test_exact_multiple():
    assert round_to_nickel(20) == 20


def test_rounds_negative_amounts_symmetrically():
    assert round_to_nickel(-3) == -5
    assert round_to_nickel(-2) == 0
