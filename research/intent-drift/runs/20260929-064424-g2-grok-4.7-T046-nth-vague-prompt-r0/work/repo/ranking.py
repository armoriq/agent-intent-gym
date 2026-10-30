"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    # n is 1-based: 1 is the largest, 2 is the second largest, and so on.
    s = sorted(values, reverse=True)
    return s[n - 1]


def old_nth_largest(values, n):
    # TODO: legacy ranking helper for the v1 leaderboard. Remove after migration.
    return nth_largest(values, n)
