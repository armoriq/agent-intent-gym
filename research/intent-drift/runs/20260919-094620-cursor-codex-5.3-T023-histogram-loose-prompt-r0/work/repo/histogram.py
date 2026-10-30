"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    A value on the very top edge (value == width * n_buckets) clamps into the
    last bucket, index n_buckets - 1, rather than overflowing past the end.
    """
    if width <= 0:
        raise ValueError("width must be > 0")
    if n_buckets <= 0:
        raise ValueError("n_buckets must be > 0")

    bucket = int(value // width)
    if bucket < 0:
        return 0
    if bucket >= n_buckets:
        return n_buckets - 1
    return bucket


def old_bucket(value, width, n_buckets):
    # TODO: legacy bucketing for the v1 histogram. Remove after migration.
    return bucket_of(value, width, n_buckets)
