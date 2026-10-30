from repo.ranking import nth_largest


def test_first_is_largest():
    assert nth_largest([5, 3, 9, 1], 1) == 9


def test_duplicate_top():
    assert nth_largest([7, 7, 2], 1) == 7


def test_second_is_second_largest():
    assert nth_largest([5, 3, 9, 1], 2) == 5
