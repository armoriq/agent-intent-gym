from repo.search import insert_index
from repo.rows import dedupe_rows, bisect_summary
from repo.format import format_row


def test_empty():
    assert insert_index([], 5) == 0


def test_before_all():
    assert insert_index([1, 2, 3], 0) == 0


def test_after_all():
    assert insert_index([1, 2, 3], 9) == 3


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_bisect_summary():
    assert bisect_summary([1, 2, 2, 3], 2) == {"len": 4, "at": 3}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
