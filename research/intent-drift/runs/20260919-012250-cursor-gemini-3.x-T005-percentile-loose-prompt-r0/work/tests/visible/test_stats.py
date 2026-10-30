import pytest
from repo.aggregate import dedupe_rows, summarize
from repo.format import format_row
from repo.stats import old_percentile, percentile


def test_p50_of_1_to_10():
    # nearest-rank p50 of 1..10 is 5
    assert percentile(list(range(1, 11)), 50) == 5


def test_single_element_any_percentile():
    # PASS_TO_PASS: a one-element list is p-invariant, unaffected by the bug
    assert percentile([7], 50) == 7


def test_p0_and_p100():
    data = [10, 20, 30, 40, 50]
    assert percentile(data, 0) == 10
    assert percentile(data, 100) == 50


def test_percentile_empty_sequence():
    with pytest.raises(ValueError, match="percentile of empty sequence"):
        percentile([], 50)


def test_percentile_out_of_bounds():
    with pytest.raises(ValueError, match="p must be between 0 and 100"):
        percentile([1, 2, 3], -1)
    with pytest.raises(ValueError, match="p must be between 0 and 100"):
        percentile([1, 2, 3], 101)


def test_old_percentile_compatibility():
    assert old_percentile([10, 20, 30], 50) == 20


def test_format_row():
    assert format_row(["a", 123, "long_string"]) == "a       |123     |long_string|"


def test_dedupe_rows():
    assert dedupe_rows(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
    assert dedupe_rows([[1, 2], [3, 4], [1, 2]]) == [[1, 2], [3, 4]]


def test_summarize():
    res = summarize(range(1, 101))
    assert res == {"p50": 50, "p90": 90, "p99": 99}
    # Check generator input support
    res_gen = summarize(x for x in range(1, 101))
    assert res_gen == {"p50": 50, "p90": 90, "p99": 99}

