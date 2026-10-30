"""Summary statistics for the reporting CLI."""


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank: rank = ceil(p/100 * n), 1-indexed; clamp to [1, n].
    # Convert to 0-indexed and clamp so p=0 -> min and p=100 -> max.
    idx = -(-(p * n) // 100) - 1  # ceil(p*n/100) - 1
    if idx < 0:
        idx = 0
    elif idx >= n:
        idx = n - 1
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
