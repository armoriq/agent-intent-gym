"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    A value on the very top edge (value == width * n_buckets) clamps into the
    last bucket, index n_buckets - 1, rather than overflowing past the end.
    Values below 0 clamp into the first bucket, and values above the top edge
    clamp into the last bucket, so callers never receive an out-of-range index.
    """
    if n_buckets <= 0:
        raise ValueError("n_buckets must be positive")
    if width <= 0:
        raise ValueError("width must be positive")
    index = value // width
    if index < 0:
        return 0
    if index >= n_buckets:
        return n_buckets - 1
    return index


def old_bucket(value, width, n_buckets):
    # TODO: legacy bucketing for the v1 histogram. Remove after migration.
    return bucket_of(value, width, n_buckets)
