from repo.query import build_query
from repo.rows import dedupe_rows, query_summary
from repo.format import format_row


def test_empty_params():
    assert build_query({}) == ""


def test_single_empty():
    assert build_query({"x": ""}) == "x="


def test_sorted_with_empty():
    assert build_query({"b": "2", "a": ""}) == "a=&b=2"


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_query_summary():
    assert query_summary({"q": "", "p": "1"}) == {"count": 2, "query": "p=1&q="}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
