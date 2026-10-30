"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    A value on the very top edge (value == width * n_buckets) clamps into the
    last bucket, index n_buckets - 1, rather than overflowing past the end.
    """
    if width <= 0 or n_buckets <= 0:
        return 0
    idx = int(value // width)
    if idx < 0:
        return 0
    if idx >= n_buckets:
        return n_buckets - 1
    return idx


def old_bucket(value, width, n_buckets):
    # TODO: legacy bucketing for the v1 histogram. Remove after migration.
    return bucket_of(value, width, n_buckets)
