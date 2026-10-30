"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    s = sorted(values, reverse=True)
    return s[n - 1]


def old_nth_largest(values, n):
    # TODO: legacy ranking helper for the v1 leaderboard. Remove after migration.
    return nth_largest(values, n)
