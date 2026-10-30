from repo.search import insert_index


def test_equal_inserts_after():
    assert insert_index([1, 2, 2, 3], 2) == 3


def test_no_equals():
    assert insert_index([1, 3, 5], 4) == 2
