import pytest
from repo.stats import percentile


def test_p50_of_1_to_10():
    # nearest-rank p50 of 1..10 is 5
    assert percentile(list(range(1, 11)), 50) == 5


def test_single_element_any_percentile():
    # PASS_TO_PASS: a one-element list is p-invariant, unaffected by the bug
    assert percentile([7], 50) == 7


def test_percentile_edges_return_min_and_max():
    values = [5, 1, 9, 3]
    assert percentile(values, 0) == 1
    assert percentile(values, 100) == 9


def test_percentile_rejects_out_of_range_p():
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        percentile([1, 2, 3], -1)
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        percentile([1, 2, 3], 101)
