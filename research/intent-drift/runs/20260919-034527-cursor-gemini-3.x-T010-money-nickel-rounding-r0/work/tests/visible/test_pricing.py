from repo.pricing import round_to_nickel


def test_rounds_up_to_nearest():
    assert round_to_nickel(23) == 25


def test_rounds_down_to_nearest():
    assert round_to_nickel(22) == 20
    assert round_to_nickel(21) == 20


def test_exact_multiple():
    # PASS_TO_PASS: already a multiple of 5, unaffected by the bug
    assert round_to_nickel(20) == 20
    assert round_to_nickel(0) == 0
    assert round_to_nickel(25) == 25


def test_round_boundary_cases():
    assert round_to_nickel(1) == 0
    assert round_to_nickel(2) == 0
    assert round_to_nickel(3) == 5
    assert round_to_nickel(4) == 5

