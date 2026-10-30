from repo.stats import percentile


def test_p50_of_1_to_10():
    # nearest-rank p50 of 1..10 is 5
    assert percentile(list(range(1, 11)), 50) == 5


def test_single_element_any_percentile():
    # PASS_TO_PASS: a one-element list is p-invariant, unaffected by the bug
    assert percentile([7], 50) == 7


def test_percentile_bounds():
    values = [10, 20, 30]
    assert percentile(values, 0) == 10
    assert percentile(values, 100) == 30


def test_percentile_rejects_out_of_range():
    values = [1, 2, 3]
    try:
        percentile(values, -1)
        assert False, "expected ValueError"
    except ValueError:
        pass

    try:
        percentile(values, 101)
        assert False, "expected ValueError"
    except ValueError:
        pass
