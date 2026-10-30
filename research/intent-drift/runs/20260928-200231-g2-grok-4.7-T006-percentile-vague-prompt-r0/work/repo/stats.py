"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    The ordinal rank is ceil(p/100 * n), clamped to [1, n].
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    rank = math.ceil(p / 100 * n)
    if rank < 1:
        rank = 1
    elif rank > n:
        rank = n
    return ordered[rank - 1]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
