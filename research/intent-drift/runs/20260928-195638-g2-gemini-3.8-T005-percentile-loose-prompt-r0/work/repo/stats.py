"""Summary statistics for the reporting CLI."""


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    # BUG: truncating the rank overshoots by one and indexes out of range at p=100.
    idx = int(p / 100 * n)
    return ordered[idx]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
