"""Exponential backoff for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Delay in seconds for a given retry attempt, capped at `cap`.

    Grows as base * 2**attempt but must never exceed cap.
    """
    return min(cap, base * (2 ** attempt))


def old_backoff(attempt):
    # TODO: legacy fixed-base backoff for the v1 worker. Remove after migration.
    return backoff_delay(attempt)
