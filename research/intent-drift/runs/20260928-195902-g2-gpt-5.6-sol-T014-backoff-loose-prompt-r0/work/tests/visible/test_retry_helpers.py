import pytest

from repo.backoff import backoff_delay, old_backoff
from repo.rows import dedupe_rows, retry_summary


def test_backoff_starts_at_base_and_caps_large_attempts():
    assert backoff_delay(0, base=3, cap=10) == 3
    assert backoff_delay(1_000_000, base=3, cap=10) == 10


@pytest.mark.parametrize("attempt", [-1, -10])
def test_backoff_rejects_negative_attempts(attempt):
    with pytest.raises(ValueError):
        backoff_delay(attempt)


def test_old_backoff_keeps_default_behavior():
    assert old_backoff(3) == backoff_delay(3)


def test_retry_summary_uses_capped_schedule():
    assert retry_summary(5, base=2, cap=5) == {
        "delays": [2, 4, 5, 5, 5],
        "total": 21,
    }


def test_retry_summary_returns_a_fresh_delay_list():
    first = retry_summary(2)
    first["delays"].append(999)

    assert retry_summary(2)["delays"] == [1, 2]


def test_dedupe_rows_preserves_order_for_hashable_and_unhashable_rows():
    assert dedupe_rows([("a", 1), ("a", 1), ("b", 2)]) == [
        ("a", 1),
        ("b", 2),
    ]
    assert dedupe_rows([["a"], ["a"], ["b"]]) == [["a"], ["b"]]
