"""Ranking helpers for the leaderboard module."""


def _sorted_desc(values):
    """Return values sorted from largest to smallest."""
    return sorted(values, reverse=True)


def nth_largest(values, n):
    """Return the nth largest value using 1-based ranking."""
    if n < 1:
        raise ValueError("n must be >= 1")

    ordered = _sorted_desc(values)
    return ordered[n - 1]


def old_nth_largest(values, n):
    """Backward-compatible alias for older ranking code paths."""
    return nth_largest(values, n)
