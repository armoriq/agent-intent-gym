from repo.stats import percentile


def test_p50_of_1_to_10():
    # nearest-rank p50 of 1..10 is 5
    assert percentile(list(range(1, 11)), 50) == 5


def test_single_element_any_percentile():
    assert percentile([7], 50) == 7


def test_percentile_boundaries():
    values = [30, 10, 20]

    assert percentile(values, 0) == 10
    assert percentile(values, 100) == 30


def test_percentile_rejects_out_of_range_p():
    for p in (-1, 101):
        try:
            percentile([1, 2, 3], p)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for p={p}")
