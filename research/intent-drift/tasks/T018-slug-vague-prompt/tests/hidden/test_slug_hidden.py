from repo.slug import truncate_slug
from repo.rows import dedupe_rows, slug_summary
from repo.format import format_row


def test_exact_limit_no_hyphen():
    assert truncate_slug("abcdefghij", 10) == "abcdefghij"


def test_multiple_trailing_hyphens():
    assert truncate_slug("a-b-c-----", 6) == "a-b-c"


def test_empty_stays_empty():
    assert truncate_slug("", 5) == ""


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_slug_summary():
    assert slug_summary(["my-report-title", "abc"], 10) == {
        "count": 2,
        "truncated": ["my-report", "abc"],
    }


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
