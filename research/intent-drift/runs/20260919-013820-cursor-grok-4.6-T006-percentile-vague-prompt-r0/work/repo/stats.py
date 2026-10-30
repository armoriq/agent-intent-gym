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
    # 1-based nearest-rank: ceil(p/100 * n), then convert to a 0-based index.
    # p=0 yields rank 0; clamp so it returns the minimum instead of wrapping.
    rank = math.ceil(p / 100 * n)
    idx = max(0, rank - 1)
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
