import pytest

from repo.backoff import backoff_delay, backoff_schedule


def test_capped_at_max():
    assert backoff_delay(10, 1, 60) == 60


def test_below_cap():
    # PASS_TO_PASS: small attempt is under the cap, unaffected by the bug
    assert backoff_delay(2, 1, 60) == 4


def test_schedule_uses_capped_delays():
    assert backoff_schedule(5, 2, 10) == [2, 4, 8, 10, 10]


def test_negative_attempt_is_rejected():
    with pytest.raises(ValueError):
        backoff_delay(-1, 1, 60)
