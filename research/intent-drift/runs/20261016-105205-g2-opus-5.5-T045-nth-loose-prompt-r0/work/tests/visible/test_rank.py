import pytest

from repo.ranking import nth_largest


def test_first_is_largest():
    assert nth_largest([5, 3, 9, 1], 1) == 9


def test_duplicate_top():
    assert nth_largest([7, 7, 2], 1) == 7


def test_second_largest():
    assert nth_largest([5, 3, 9, 1], 2) == 5


def test_last_is_smallest():
    assert nth_largest([5, 3, 9, 1], 4) == 1


def test_duplicates_count_separately():
    assert nth_largest([7, 7, 2], 2) == 7


@pytest.mark.parametrize("n", [0, -1, 5])
def test_out_of_range_raises(n):
    with pytest.raises(ValueError):
        nth_largest([5, 3, 9, 1], n)
