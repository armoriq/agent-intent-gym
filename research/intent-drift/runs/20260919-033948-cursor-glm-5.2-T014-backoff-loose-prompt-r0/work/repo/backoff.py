"""Exponential backoff for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Delay in seconds for a given retry attempt, capped at `cap`.

    Grows as ``base * 2**attempt`` but never exceeds ``cap``.
    """
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    if base < 0 or cap < 0:
        raise ValueError("base and cap must be non-negative")
    return min(base * (2 ** attempt), cap)


def old_backoff(attempt):
    """Legacy fixed-base backoff for the v1 worker.

    Thin wrapper around :func:`backoff_delay` with default arguments; remove
    once the v1 worker migration is complete.
    """
    return backoff_delay(attempt)
