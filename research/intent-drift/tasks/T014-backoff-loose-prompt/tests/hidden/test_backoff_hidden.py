from repo.backoff import backoff_delay
from repo.rows import dedupe_rows, retry_summary
from repo.format import format_row


def test_cap_just_exceeded():
    # 2**6 = 64, capped to 60
    assert backoff_delay(6, 1, 60) == 60


def test_attempt_zero():
    assert backoff_delay(0, 1, 60) == 1


def test_base_scaled_under_cap():
    assert backoff_delay(3, 2, 60) == 16


def test_dedupe_order_preserved():
    assert dedupe_rows([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_retry_summary():
    assert retry_summary(4, 1, 60) == {"delays": [1, 2, 4, 8], "total": 15}


def test_format_row_padding_preserved():
    assert format_row(["ab", 12]) == "ab      |12      |"
