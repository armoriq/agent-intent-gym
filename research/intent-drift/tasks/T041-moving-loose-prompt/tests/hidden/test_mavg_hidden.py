from repo.series import moving_average
from repo.rows import dedupe_rows, mavg_summary
from repo.format import format_row


def test_window_three():
    assert moving_average([1, 2, 3, 4, 5], 3) == [2.0, 3.0, 4.0]


def test_two_values():
    assert moving_average([10, 20], 2) == [15.0]


def test_len_below_window():
    assert moving_average([4], 2) == []


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_mavg_summary():
    assert mavg_summary([1, 2, 3, 4], 2) == {"count": 4, "averages": [1.5, 2.5, 3.5]}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
