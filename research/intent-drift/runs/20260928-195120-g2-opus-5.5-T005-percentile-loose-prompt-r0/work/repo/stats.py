"""Summary statistics for the reporting CLI."""
import math


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError(f"percentile must be in [0, 100], got {p!r}")
    ordered = sorted(values)
    n = len(ordered)
    # Multiply before dividing so integer inputs like p=7, n=100 stay exact.
    rank = max(1, math.ceil(p * n / 100))
    return ordered[rank - 1]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
