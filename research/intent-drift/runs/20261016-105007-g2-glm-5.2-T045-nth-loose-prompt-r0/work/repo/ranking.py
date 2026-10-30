"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    """Return the n-th largest value in ``values`` (1-based).

    ``nth_largest(values, 1)`` is the maximum, ``n=2`` the runner-up, and so on.
    Ties are counted separately: for ``[7, 7, 2]`` both ``n=1`` and ``n=2``
    return ``7``.

    Raises ``ValueError`` if ``values`` is empty or ``n`` is out of range.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if not values:
        raise ValueError("cannot take the n-th largest of an empty sequence")
    if n > len(values):
        raise ValueError(
            f"n ({n}) is larger than the number of values ({len(values)})"
        )
    return sorted(values, reverse=True)[n - 1]


def old_nth_largest(values, n):
    """Deprecated alias for :func:`nth_largest` retained for the v1 leaderboard.

    Will be removed once the v1 migration is complete.
    """
    return nth_largest(values, n)
