"""Summary statistics for the reporting CLI."""
from math import ceil


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if p < 0 or p > 100:
        raise ValueError("percentile p must be in [0, 100]")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank definition: rank = ceil((p/100) * n), then convert to 0-based.
    # Clamp p=0 to the minimum (first element).
    idx = 0 if p == 0 else ceil((p / 100) * n) - 1
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
