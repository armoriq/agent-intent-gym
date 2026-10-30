"""Summary statistics for the reporting CLI."""

import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("percentile must be between 0 and 100")

    ordered = sorted(values)
    n = len(ordered)
    idx = max(0, math.ceil(p / 100 * n) - 1)
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
