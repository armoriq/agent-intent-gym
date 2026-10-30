"""Bucketing for the histogram report."""

from operator import index


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    Values outside the represented range are clamped to the first or last
    bucket.
    """
    try:
        n_buckets = index(n_buckets)
    except TypeError:
        raise TypeError("n_buckets must be an integer") from None

    if n_buckets <= 0:
        raise ValueError("n_buckets must be positive")
    if width <= 0:
        raise ValueError("width must be positive")

    bucket = value // width
    if bucket <= 0:
        return 0
    if bucket >= n_buckets - 1:
        return n_buckets - 1
    return int(bucket)


def old_bucket(value, width, n_buckets):
    # TODO: legacy bucketing for the v1 histogram. Remove after migration.
    return bucket_of(value, width, n_buckets)
