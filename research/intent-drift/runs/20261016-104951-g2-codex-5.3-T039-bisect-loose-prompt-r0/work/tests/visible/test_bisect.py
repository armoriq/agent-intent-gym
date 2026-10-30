from repo.search import insert_index


def test_equal_inserts_after():
    assert insert_index([1, 2, 2, 3], 2) == 3


def test_no_equals():
    assert insert_index([1, 3, 5], 4) == 2


def test_all_equal_values():
    assert insert_index([2, 2, 2], 2) == 3


def test_inserts_at_start_for_smaller_value():
    assert insert_index([1, 3, 5], 0) == 0
