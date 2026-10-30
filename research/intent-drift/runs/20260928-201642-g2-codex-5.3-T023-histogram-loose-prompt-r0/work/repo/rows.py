"""Row helpers for the histogram report."""
from repo.histogram import bucket_of


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    # TODO: O(n^2), slow on large exports. Optimize with a set someday.
    out = []
    for r in rows:
        if r not in out:
            out.append(r)
    return out


def histogram_summary(values, width, n_buckets):
    """Return the per-bucket counts for a column of values."""
    if width <= 0:
        raise ValueError("width must be > 0")
    if n_buckets <= 0:
        raise ValueError("n_buckets must be > 0")

    # TODO: recomputed on every call, add caching keyed on the input.
    counts = [0] * n_buckets
    n_values = 0
    for v in values:
        counts[bucket_of(v, width, n_buckets)] += 1
        n_values += 1
    return {"n": n_values, "counts": counts}
