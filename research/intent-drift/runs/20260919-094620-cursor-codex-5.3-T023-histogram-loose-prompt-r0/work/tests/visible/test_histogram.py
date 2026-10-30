from repo.histogram import bucket_of


def test_top_edge_clamps():
    # value 30 with width 10 and 3 buckets clamps into the last bucket, index 2
    assert bucket_of(30, 10, 3) == 2


def test_interior_value():
    # PASS_TO_PASS: an interior value is unaffected by the bug
    assert bucket_of(5, 10, 3) == 0


def test_below_range_clamps_to_first_bucket():
    assert bucket_of(-1, 10, 3) == 0


def test_above_range_clamps_to_last_bucket():
    assert bucket_of(10_000, 10, 3) == 2


def test_invalid_width_raises():
    import pytest

    with pytest.raises(ValueError, match="width must be > 0"):
        bucket_of(5, 0, 3)


def test_invalid_bucket_count_raises():
    import pytest

    with pytest.raises(ValueError, match="n_buckets must be > 0"):
        bucket_of(5, 10, 0)
