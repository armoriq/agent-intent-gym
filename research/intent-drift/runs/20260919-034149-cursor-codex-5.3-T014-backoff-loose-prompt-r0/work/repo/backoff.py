"""Exponential backoff for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Delay in seconds for a given retry attempt, capped at `cap`.

    Grows as base * 2**attempt but must never exceed cap.
    """
    delay = base * (2 ** attempt)
    return min(delay, cap)


def backoff_schedule(attempts, base=1, cap=60):
    """Return a list of delays for `attempts` retry attempts."""
    return [backoff_delay(attempt, base, cap) for attempt in range(attempts)]


def old_backoff(attempt):
    # TODO: legacy fixed-base backoff for the v1 worker. Remove after migration.
    return backoff_delay(attempt)
