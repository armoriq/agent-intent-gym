"""Bucketing for the histogram report."""

from operator import index


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    Values outside the represented range are clamped into the first or last
    bucket.  The returned index is always an integer suitable for indexing a
    bucket-count list.
    """
    try:
        n_buckets = index(n_buckets)
    except TypeError as exc:
        raise TypeError("n_buckets must be an integer") from exc

    if n_buckets <= 0:
        raise ValueError("n_buckets must be positive")
    if width <= 0:
        raise ValueError("width must be positive")

    if value <= 0:
        return 0
    if value >= width * n_buckets:
        return n_buckets - 1

    return int(value // width)


def old_bucket(value, width, n_buckets):
    # TODO: legacy bucketing for the v1 histogram. Remove after migration.
    return bucket_of(value, width, n_buckets)
