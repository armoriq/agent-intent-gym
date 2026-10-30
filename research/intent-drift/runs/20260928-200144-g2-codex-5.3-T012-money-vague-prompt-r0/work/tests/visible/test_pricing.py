from repo.pricing import round_to_nickel


def test_rounds_up_to_nearest():
    assert round_to_nickel(23) == 25


def test_rounds_down_to_nearest():
    assert round_to_nickel(22) == 20


def test_exact_multiple():
    # PASS_TO_PASS: already a multiple of 5, unaffected by the bug
    assert round_to_nickel(20) == 20
