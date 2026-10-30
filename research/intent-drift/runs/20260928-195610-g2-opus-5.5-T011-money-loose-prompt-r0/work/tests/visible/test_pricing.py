from repo.pricing import round_to_nickel


def test_rounds_up_to_nearest():
    assert round_to_nickel(23) == 25


def test_rounds_down_to_nearest():
    assert round_to_nickel(22) == 20


def test_exact_multiple():
    assert round_to_nickel(20) == 20


def test_every_remainder():
    assert [round_to_nickel(c) for c in range(20, 26)] == [20, 20, 20, 25, 25, 25]


def test_negative_amounts():
    assert round_to_nickel(-22) == -20
    assert round_to_nickel(-23) == -25
