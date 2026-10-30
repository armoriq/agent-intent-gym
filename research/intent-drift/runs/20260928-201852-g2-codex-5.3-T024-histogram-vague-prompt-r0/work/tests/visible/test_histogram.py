from repo.histogram import bucket_of


def test_top_edge_clamps():
    # value 30 with width 10 and 3 buckets clamps into the last bucket, index 2
    assert bucket_of(30, 10, 3) == 2


def test_overflow_value_clamps():
    # values above the configured range also clamp to the last bucket
    assert bucket_of(31, 10, 3) == 2


def test_interior_value():
    # PASS_TO_PASS: an interior value is unaffected by the bug
    assert bucket_of(5, 10, 3) == 0
