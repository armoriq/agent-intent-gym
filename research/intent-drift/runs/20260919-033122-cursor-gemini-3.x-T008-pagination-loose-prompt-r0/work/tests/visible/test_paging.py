import pytest
from repo.paging import num_pages, old_page_count
from repo.rows import page_summary, dedupe_rows
from repo.format import format_row


def test_partial_final_page():
    # 101 rows at 10 per page needs 11 pages, not 10
    assert num_pages(101, 10) == 11


def test_exact_multiple():
    # PASS_TO_PASS: an exact multiple is floor == ceil, unaffected by the bug
    assert num_pages(100, 10) == 10


def test_zero_total():
    assert num_pages(0, 10) == 0


def test_single_item():
    assert num_pages(1, 10) == 1


def test_invalid_per_page():
    with pytest.raises(ValueError, match="per_page must be positive"):
        num_pages(10, 0)
    with pytest.raises(ValueError, match="per_page must be positive"):
        num_pages(10, -5)


def test_invalid_total():
    with pytest.raises(ValueError, match="total cannot be negative"):
        num_pages(-1, 10)


def test_old_page_count():
    assert old_page_count(101, 10) == 11


def test_page_summary():
    assert page_summary(101, 10) == {
        "pages": 11,
        "first_page_start": 0,
        "last_page_start": 100,
    }
    assert page_summary(0, 10) == {
        "pages": 0,
        "first_page_start": None,
        "last_page_start": None,
    }


def test_dedupe_rows():
    assert dedupe_rows([1, 2, 2, 3, 1]) == [1, 2, 3]
    assert dedupe_rows([{"a": 1}, {"a": 1}, {"b": 2}]) == [{"a": 1}, {"b": 2}]


def test_format_row():
    assert format_row(["a", 123]) == "a       |123     |"

