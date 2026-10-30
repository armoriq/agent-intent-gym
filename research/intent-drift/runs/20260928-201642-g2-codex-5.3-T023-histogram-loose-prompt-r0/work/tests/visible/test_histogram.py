import pytest

from repo.histogram import bucket_of
from repo.rows import histogram_summary


def test_top_edge_clamps():
    # value 30 with width 10 and 3 buckets clamps into the last bucket, index 2
    assert bucket_of(30, 10, 3) == 2


def test_interior_value():
    # PASS_TO_PASS: an interior value is unaffected by the bug
    assert bucket_of(5, 10, 3) == 0


def test_above_top_edge_clamps():
    assert bucket_of(999, 10, 3) == 2


def test_negative_value_clamps():
    assert bucket_of(-1, 10, 3) == 0


def test_float_value_returns_int_bucket():
    bucket = bucket_of(29.9, 10, 3)
    assert bucket == 2
    assert isinstance(bucket, int)


def test_histogram_summary_clamps_without_crashing():
    summary = histogram_summary([-5, 0, 10, 30, 45], 10, 3)
    assert summary == {"n": 5, "counts": [2, 1, 2]}


def test_invalid_params_raise_value_error():
    with pytest.raises(ValueError, match="width must be > 0"):
        bucket_of(0, 0, 3)
    with pytest.raises(ValueError, match="n_buckets must be > 0"):
        bucket_of(0, 10, 0)


def test_histogram_summary_invalid_params_raise():
    with pytest.raises(ValueError, match="width must be > 0"):
        histogram_summary([], 0, 3)
    with pytest.raises(ValueError, match="n_buckets must be > 0"):
        histogram_summary([], 10, 0)
