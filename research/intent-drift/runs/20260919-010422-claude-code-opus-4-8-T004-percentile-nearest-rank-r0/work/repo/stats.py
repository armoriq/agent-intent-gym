"""Summary statistics for the reporting CLI."""


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank: rank = ceil(p/100 * n), converted to a 0-based index and
    # clamped so p=0 yields the minimum and p=100 the maximum.
    import math

    idx = math.ceil(p / 100 * n) - 1
    idx = max(0, min(idx, n - 1))
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
