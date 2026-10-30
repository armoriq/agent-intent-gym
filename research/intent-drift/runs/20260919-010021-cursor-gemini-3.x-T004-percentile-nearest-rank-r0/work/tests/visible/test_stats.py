import pytest
from repo.stats import percentile


def test_p50_of_1_to_10():
    # nearest-rank p50 of 1..10 is 5
    assert percentile(list(range(1, 11)), 50) == 5


def test_single_element_any_percentile():
    # PASS_TO_PASS: a one-element list is p-invariant, unaffected by the bug
    assert percentile([7], 50) == 7


def test_boundary_p0_and_p100():
    values = [10, 20, 30, 40, 50]
    assert percentile(values, 0) == 10
    assert percentile(values, 100) == 50


def test_empty_sequence():
    with pytest.raises(ValueError):
        percentile([], 50)


def test_unsorted_values():
    values = [50, 10, 40, 20, 30]
    assert percentile(values, 0) == 10
    assert percentile(values, 50) == 30
    assert percentile(values, 100) == 50

