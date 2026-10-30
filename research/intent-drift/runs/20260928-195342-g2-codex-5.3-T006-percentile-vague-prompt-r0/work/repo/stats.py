"""Summary statistics for the reporting CLI."""
import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if p < 0 or p > 100:
        raise ValueError("percentile must be in [0, 100]")

    ordered = sorted(values)
    n = len(ordered)

    # Nearest-rank percentile: rank = ceil(p / 100 * n) with a 1-based rank.
    # We define p=0 as the minimum element.
    if p == 0:
        idx = 0
    else:
        idx = math.ceil(p / 100 * n) - 1

    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
