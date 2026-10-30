import pytest

from repo.series import moving_average, old_moving_average


def test_includes_final_window():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]


def test_shorter_than_window():
    assert moving_average([5], 2) == []


def test_exact_window_size():
    assert moving_average([2, 4, 6], 3) == [4.0]


def test_legacy_alias_matches_primary_helper():
    values = [1, 2, 3, 4]
    assert old_moving_average(values, 2) == moving_average(values, 2)


def test_non_positive_window_raises():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 0)
