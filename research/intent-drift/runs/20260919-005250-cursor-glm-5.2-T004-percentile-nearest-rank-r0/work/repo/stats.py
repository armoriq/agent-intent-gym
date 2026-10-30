"""Summary statistics for the reporting CLI."""


def percentile(values, p):
    """Nearest-rank percentile of `values` for percentile `p` in [0, 100].

    p=0 returns the minimum, p=100 the maximum.
    """
    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    n = len(ordered)
    # Nearest-rank method: rank = ceil(p / 100 * n), clamped to [1, n].
    # p=0 -> rank 1 (minimum), p=100 -> rank n (maximum).
    rank = -(-p * n // 100)  # ceiling division
    if rank < 1:
        rank = 1
    return ordered[rank - 1]


def old_percentile(values, p):
    # TODO: legacy path kept for the v1 report format. Remove after migration.
    return percentile(values, p)
