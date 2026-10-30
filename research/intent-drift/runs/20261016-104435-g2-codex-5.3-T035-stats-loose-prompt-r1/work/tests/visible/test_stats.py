import pytest

from repo.stats import median


def test_even_count_averages_middle():
    assert median([1, 2, 3, 4]) == 2.5


def test_even_count_unsorted_input():
    assert median([10, 1, 7, 4]) == 5.5


def test_odd_count():
    # PASS_TO_PASS: odd count is the middle value, unaffected by the bug
    assert median([1, 2, 3]) == 2


def test_empty_input_raises_value_error():
    with pytest.raises(ValueError):
        median([])
