"""Row helpers for the histogram report."""
from repo.histogram import bucket_of


def dedupe_rows(rows):
    """Drop duplicate rows, keeping first-seen order."""
    out = []
    seen = set()
    for r in rows:
        try:
            if r not in seen:
                seen.add(r)
                out.append(r)
        except TypeError:
            if r not in out:
                out.append(r)
    return out


def histogram_summary(values, width, n_buckets):
    """Return the per-bucket counts for a column of values."""
    counts = [0] * max(0, n_buckets)
    if n_buckets <= 0:
        return {"n": len(values), "counts": counts}
    for v in values:
        counts[bucket_of(v, width, n_buckets)] += 1
    return {"n": len(values), "counts": counts}
