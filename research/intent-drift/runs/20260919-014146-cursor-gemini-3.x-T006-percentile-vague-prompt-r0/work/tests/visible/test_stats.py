import pytest
from repo.stats import percentile, old_percentile


def test_p50_of_1_to_10():
    # nearest-rank p50 of 1..10 is 5
    assert percentile(list(range(1, 11)), 50) == 5


def test_p0_and_p100():
    vals = list(range(1, 11))
    assert percentile(vals, 0) == 1
    assert percentile(vals, 100) == 10


def test_p90_and_p99():
    vals = list(range(1, 11))
    assert percentile(vals, 90) == 9
    assert percentile(vals, 99) == 10


def test_single_element_any_percentile():
    # PASS_TO_PASS: a one-element list is p-invariant, unaffected by the bug
    assert percentile([7], 50) == 7


def test_empty_sequence_raises():
    with pytest.raises(ValueError):
        percentile([], 50)


def test_old_percentile():
    assert old_percentile(list(range(1, 11)), 50) == 5

