"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[-1]
    rank = math.ceil(p / 100 * n)
    return ordered[rank - 1]
