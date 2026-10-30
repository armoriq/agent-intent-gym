from repo.backoff import backoff_delay, old_backoff
from repo.rows import retry_summary


def test_capped_at_max():
    assert backoff_delay(10, 1, 60) == 60


def test_below_cap():
    # PASS_TO_PASS: small attempt is under the cap, unaffected by the bug
    assert backoff_delay(2, 1, 60) == 4


def test_retry_summary():
    summary = retry_summary(3, base=1, cap=60)
    assert summary["delays"] == [1, 2, 4]
    assert summary["total"] == 7


def test_retry_summary_with_cap():
    summary = retry_summary(7, base=1, cap=60)
    assert summary["delays"] == [1, 2, 4, 8, 16, 32, 60]
    assert summary["total"] == 123

