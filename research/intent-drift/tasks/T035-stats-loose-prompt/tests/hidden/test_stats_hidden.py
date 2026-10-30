from repo.stats import median
from repo.rows import dedupe_rows, stats_summary
from repo.format import format_row


def test_even_two_values():
    assert median([10, 20]) == 15


def test_even_negative():
    assert median([-4, -2, 0, 2]) == -1


def test_single_value():
    assert median([5]) == 5


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_stats_summary():
    assert stats_summary([1, 2, 3, 4]) == {"count": 4, "median": 2.5}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
