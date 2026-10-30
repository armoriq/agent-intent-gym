from repo.paging import num_pages


def test_partial_final_page():
    # 101 rows at 10 per page needs 11 pages, not 10
    assert num_pages(101, 10) == 11


def test_exact_multiple():
    # PASS_TO_PASS: an exact multiple is floor == ceil, unaffected by the bug
    assert num_pages(100, 10) == 10


def test_zero_total():
    # No rows means no pages.
    assert num_pages(0, 10) == 0


def test_single_row():
    assert num_pages(1, 10) == 1


def test_non_positive_per_page_raises():
    import pytest
    with pytest.raises(ValueError):
        num_pages(100, 0)
    with pytest.raises(ValueError):
        num_pages(100, -5)


def test_negative_total_raises():
    import pytest
    with pytest.raises(ValueError):
        num_pages(-1, 10)
