from repo.backoff import backoff_delay, backoff_schedule
from repo.rows import retry_summary


def test_capped_at_max():
    assert backoff_delay(10, 1, 60) == 60


def test_below_cap():
    # PASS_TO_PASS: small attempt is under the cap, unaffected by the bug
    assert backoff_delay(2, 1, 60) == 4


def test_schedule_respects_cap_each_attempt():
    assert backoff_schedule(5, base=10, cap=25) == [10, 20, 25, 25, 25]


def test_retry_summary_matches_schedule_and_total():
    summary = retry_summary(4, base=2, cap=10)
    assert summary == {"delays": [2, 4, 8, 10], "total": 24}
