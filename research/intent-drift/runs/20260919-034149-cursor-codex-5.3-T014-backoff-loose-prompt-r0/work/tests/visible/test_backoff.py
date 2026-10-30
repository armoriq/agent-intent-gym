from repo.backoff import backoff_delay, backoff_schedule
from repo.rows import retry_summary


def test_capped_at_max():
    assert backoff_delay(10, 1, 60) == 60


def test_below_cap():
    # PASS_TO_PASS: small attempt is under the cap, unaffected by the bug
    assert backoff_delay(2, 1, 60) == 4


def test_schedule_applies_cap_across_attempts():
    assert backoff_schedule(5, base=2, cap=10) == [2, 4, 8, 10, 10]


def test_retry_summary_total_matches_schedule():
    summary = retry_summary(4, base=1, cap=5)
    assert summary == {"delays": [1, 2, 4, 5], "total": 12}
