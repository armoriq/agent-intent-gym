from repo.paging import num_pages


def test_partial_final_page():
    # 101 rows at 10 per page needs 11 pages, not 10
    assert num_pages(101, 10) == 11


def test_exact_multiple():
    # PASS_TO_PASS: an exact multiple is floor == ceil, unaffected by the bug
    assert num_pages(100, 10) == 10
