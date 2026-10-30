import pytest

from repo.histogram import bucket_of
from repo.rows import dedupe_rows, histogram_summary
from repo.format import format_row


def test_top_edge_clamps():
    # value 30 with width 10 and 3 buckets clamps into the last bucket, index 2
    assert bucket_of(30, 10, 3) == 2


def test_interior_value():
    # PASS_TO_PASS: an interior value is unaffected by the bug
    assert bucket_of(5, 10, 3) == 0


def test_exact_bucket_boundaries():
    assert bucket_of(0, 10, 3) == 0
    assert bucket_of(10, 10, 3) == 1
    assert bucket_of(20, 10, 3) == 2


def test_values_beyond_top_edge_clamp():
    assert bucket_of(31, 10, 3) == 2
    assert bucket_of(100, 10, 3) == 2


def test_negative_value_rejected():
    with pytest.raises(ValueError):
        bucket_of(-1, 10, 3)


def test_invalid_width_rejected():
    with pytest.raises(ValueError):
        bucket_of(5, 0, 3)
    with pytest.raises(ValueError):
        bucket_of(5, -1, 3)


def test_invalid_n_buckets_rejected():
    with pytest.raises(ValueError):
        bucket_of(5, 10, 0)
    with pytest.raises(ValueError):
        bucket_of(5, 10, -1)


def test_histogram_summary_counts():
    values = [0, 5, 10, 15, 20, 25, 30, 100]
    assert histogram_summary(values, 10, 3) == {
        "n": 8,
        "counts": [2, 2, 4],
    }


def test_dedupe_rows_preserves_order():
    assert dedupe_rows([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]


def test_format_row_pads_and_delimits():
    assert format_row(["a", "bb", 123]) == "a       |bb      |123     |"


def test_format_row_custom_width():
    assert format_row(["x", "yy"], width=4) == "x   |yy  |"
