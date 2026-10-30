"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("percentile p must be in [0, 100]")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank: rank = ceil(p/100 * n), clamped to [1, n], index = rank - 1.
    rank = math.ceil(p / 100 * n)
    idx = max(1, rank) - 1
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
