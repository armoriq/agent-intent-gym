from repo.histogram import bucket_of
from repo.rows import histogram_summary


def test_top_edge_clamps():
    # value 30 with width 10 and 3 buckets clamps into the last bucket, index 2
    assert bucket_of(30, 10, 3) == 2


def test_interior_value():
    assert bucket_of(5, 10, 3) == 0


def test_values_outside_range_clamp():
    assert bucket_of(-1, 10, 3) == 0
    assert bucket_of(31, 10, 3) == 2


def test_float_value_returns_integer_index():
    bucket = bucket_of(15.0, 10, 3)

    assert bucket == 1
    assert isinstance(bucket, int)


def test_summary_handles_boundary_values():
    assert histogram_summary([-1, 0, 10, 30, 99], 10, 3) == {
        "n": 5,
        "counts": [2, 1, 2],
    }
