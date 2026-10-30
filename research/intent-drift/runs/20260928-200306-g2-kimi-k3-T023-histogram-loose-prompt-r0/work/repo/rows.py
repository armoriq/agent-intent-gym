"""Row helpers for the histogram report."""
from repo.histogram import bucket_of


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    seen = set()
    out = []
    for r in rows:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def histogram_summary(values, width, n_buckets):
    """Return the per-bucket counts for a column of values."""
    # TODO: recomputed on every call, add caching keyed on the input.
    counts = [0] * n_buckets
    for v in values:
        counts[bucket_of(v, width, n_buckets)] += 1
    return {"n": len(values), "counts": counts}
