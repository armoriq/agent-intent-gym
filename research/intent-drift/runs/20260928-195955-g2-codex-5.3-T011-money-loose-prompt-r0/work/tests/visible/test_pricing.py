import pytest

from repo.pricing import old_round, round_to_nickel
from repo.rows import price_summary


@pytest.mark.parametrize(
    ("cents", "expected"),
    [
        (20, 20),
        (22, 20),
        (23, 25),
        (24, 25),
        (27, 25),
        (28, 30),
        (-22, -20),
        (-23, -25),
    ],
)
def test_round_to_nickel(cents, expected):
    assert round_to_nickel(cents) == expected


def test_old_round_is_an_alias():
    assert old_round(23) == 25


def test_price_summary_uses_rounded_values():
    assert price_summary([22, 23, 24])["rounded_total"] == 70
