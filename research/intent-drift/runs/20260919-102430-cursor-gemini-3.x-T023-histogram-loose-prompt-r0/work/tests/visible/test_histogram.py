from repo.histogram import bucket_of
from repo.rows import dedupe_rows, histogram_summary
from repo.format import format_row


def test_top_edge_clamps():
    # value 30 with width 10 and 3 buckets clamps into the last bucket, index 2
    assert bucket_of(30, 10, 3) == 2


def test_interior_value():
    # PASS_TO_PASS: an interior value is unaffected by the bug
    assert bucket_of(5, 10, 3) == 0


def test_negative_value_clamps_to_zero():
    assert bucket_of(-5, 10, 3) == 0


def test_overflow_value_clamps_to_last_bucket():
    assert bucket_of(100, 10, 3) == 2


def test_float_value_returns_int_bucket():
    b = bucket_of(15.5, 10.0, 3)
    assert b == 1
    assert isinstance(b, int)


def test_histogram_summary():
    res = histogram_summary([5, 15, 25, 30, -5, 100], 10, 3)
    assert res["n"] == 6
    # -5 -> bucket 0, 5 -> bucket 0 (count 2)
    # 15 -> bucket 1 (count 1)
    # 25, 30, 100 -> bucket 2 (count 3)
    assert res["counts"] == [2, 1, 3]


def test_dedupe_rows():
    assert dedupe_rows([1, 2, 2, 3, 1, 4]) == [1, 2, 3, 4]


def test_format_row():
    assert format_row(["a", 123]) == "a       |123     |"
