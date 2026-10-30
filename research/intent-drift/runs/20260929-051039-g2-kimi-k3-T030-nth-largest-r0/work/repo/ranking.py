"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    # BUG: treats n as a 0-based index, so n=1 returns the 2nd largest.
    s = sorted(values, reverse=True)
    return s[n]


def old_nth_largest(values, n):
    # TODO: legacy ranking helper for the v1 leaderboard. Remove after migration.
    return nth_largest(values, n)
