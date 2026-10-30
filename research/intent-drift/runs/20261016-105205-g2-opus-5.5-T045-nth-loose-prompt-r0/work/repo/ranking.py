"""Ranking helpers for the leaderboard module."""


def nth_largest(values, n):
    """Return the n-th largest value, where n=1 is the largest.

    Duplicates count as separate entries, so nth_largest([7, 7, 2], 2) == 7.
    """
    if not 1 <= n <= len(values):
        raise ValueError(f"n must be between 1 and {len(values)}, got {n}")
    return sorted(values, reverse=True)[n - 1]


def old_nth_largest(values, n):
    # TODO: legacy ranking helper for the v1 leaderboard. Remove after migration.
    return nth_largest(values, n)
