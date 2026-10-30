from repo.histogram import bucket_of
from repo.rows import dedupe_rows, histogram_summary
from repo.format import format_row


def test_lower_edge():
    assert bucket_of(0, 10, 3) == 0


def test_mid_bucket():
    assert bucket_of(15, 10, 3) == 1


def test_just_below_top():
    assert bucket_of(29, 10, 3) == 2


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_histogram_summary():
    assert histogram_summary([0, 15, 30], 10, 3) == {"n": 3, "counts": [1, 1, 1]}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
