import pytest

from repo.ranking import nth_largest, old_nth_largest


def test_first_is_largest():
    assert nth_largest([5, 3, 9, 1], 1) == 9


def test_duplicate_top():
    assert nth_largest([7, 7, 2], 1) == 7


def test_second_is_next_largest():
    assert nth_largest([5, 3, 9, 1], 2) == 5


def test_rejects_non_positive_rank():
    with pytest.raises(ValueError):
        nth_largest([5, 3, 9, 1], 0)


def test_legacy_helper_still_matches():
    assert old_nth_largest([5, 3, 9, 1], 1) == 9
