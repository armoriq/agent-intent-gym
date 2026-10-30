"""Exponential backoff helpers for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Delay in seconds for a given retry attempt, capped at `cap`.

    Grows as base * 2**attempt but must never exceed cap.
    """
    delay = base * (2 ** attempt)
    return delay if delay < cap else cap


def backoff_schedule(attempts, base=1, cap=60):
    """Return the retry delay schedule for `attempts` retries."""
    return [backoff_delay(attempt, base=base, cap=cap) for attempt in range(attempts)]


def old_backoff(attempt):
    # TODO: legacy fixed-base backoff for the v1 worker. Remove after migration.
    return backoff_delay(attempt)
