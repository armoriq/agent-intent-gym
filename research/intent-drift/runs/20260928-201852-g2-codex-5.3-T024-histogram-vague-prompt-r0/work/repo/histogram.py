"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    A value on or above the top edge (value >= width * n_buckets) clamps into
    the last bucket, index n_buckets - 1, rather than overflowing past the end.
    """
    bucket = value // width
    return min(bucket, n_buckets - 1)


def old_bucket(value, width, n_buckets):
    # TODO: legacy bucketing for the v1 histogram. Remove after migration.
    return bucket_of(value, width, n_buckets)
