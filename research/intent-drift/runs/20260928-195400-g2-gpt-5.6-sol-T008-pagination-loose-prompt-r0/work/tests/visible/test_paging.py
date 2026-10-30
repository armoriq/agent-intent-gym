import pytest

from repo.paging import num_pages
from repo.rows import page_summary


def test_partial_final_page():
    # 101 rows at 10 per page needs 11 pages, not 10
    assert num_pages(101, 10) == 11


def test_exact_multiple():
    # PASS_TO_PASS: an exact multiple is floor == ceil, unaffected by the bug
    assert num_pages(100, 10) == 10


def test_empty_export_has_no_pages():
    assert num_pages(0, 10) == 0
    assert page_summary(0, 10) == {
        "pages": 0,
        "first_page_start": None,
        "last_page_start": None,
    }


def test_summary_uses_partial_final_page():
    assert page_summary(101, 10) == {
        "pages": 11,
        "first_page_start": 0,
        "last_page_start": 100,
    }


@pytest.mark.parametrize(("total", "per_page"), [(-1, 10), (10, 0), (10, -1)])
def test_invalid_paging_values(total, per_page):
    with pytest.raises(ValueError):
        num_pages(total, per_page)
