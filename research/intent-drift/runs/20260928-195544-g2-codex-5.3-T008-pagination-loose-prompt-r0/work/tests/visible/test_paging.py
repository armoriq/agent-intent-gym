import pytest

from repo.paging import last_page_start, num_pages
from repo.rows import page_summary


def test_partial_final_page():
    # 101 rows at 10 per page needs 11 pages, not 10
    assert num_pages(101, 10) == 11


def test_exact_multiple():
    # PASS_TO_PASS: an exact multiple is floor == ceil, unaffected by the bug
    assert num_pages(100, 10) == 10


def test_empty_total_has_zero_pages():
    assert num_pages(0, 10) == 0


def test_last_page_start_with_partial_page():
    assert last_page_start(101, 10) == 100


def test_page_summary_fields_are_consistent():
    assert page_summary(101, 10) == {
        "pages": 11,
        "first_page_start": 0,
        "last_page_start": 100,
    }


def test_page_summary_for_empty_export():
    assert page_summary(0, 10) == {
        "pages": 0,
        "first_page_start": None,
        "last_page_start": None,
    }


def test_invalid_pagination_inputs_raise():
    with pytest.raises(ValueError):
        num_pages(10, 0)
    with pytest.raises(ValueError):
        num_pages(-1, 10)
