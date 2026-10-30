"""Exponential backoff helpers for the retry layer."""


def backoff_delay(attempt, base=1, cap=60):
    """Return retry delay in seconds for one attempt.

    The delay grows as ``base * 2**attempt`` and is capped at ``cap``.
    """
    if attempt < 0:
        raise ValueError("attempt must be >= 0")
    if base <= 0:
        raise ValueError("base must be > 0")
    if cap <= 0:
        raise ValueError("cap must be > 0")

    return min(base * (2 ** attempt), cap)


def backoff_schedule(attempts, base=1, cap=60):
    """Return the per-attempt delay schedule for ``attempts`` retries."""
    if attempts < 0:
        raise ValueError("attempts must be >= 0")
    return [backoff_delay(attempt, base, cap) for attempt in range(attempts)]


def old_backoff(attempt):
    # Legacy fixed-base backoff retained for v1 worker compatibility.
    return backoff_delay(attempt)
