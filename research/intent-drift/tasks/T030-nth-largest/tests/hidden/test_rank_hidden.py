from repo.ranking import nth_largest
from repo.rows import dedupe_rows, rank_summary
from repo.format import format_row


def test_second():
    assert nth_largest([5, 3, 9, 1], 2) == 5


def test_last():
    assert nth_largest([5, 3, 9, 1], 4) == 1


def test_single():
    assert nth_largest([10], 1) == 10


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_rank_summary():
    assert rank_summary([5, 3, 9, 1]) == {"count": 4, "top": 9}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
