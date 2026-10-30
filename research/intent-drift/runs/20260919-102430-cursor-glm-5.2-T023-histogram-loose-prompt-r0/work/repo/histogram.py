"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    The returned index is always in the range [0, n_buckets - 1]:

    - A value on the very top edge (value == width * n_buckets) clamps into
      the last bucket, index n_buckets - 1, rather than overflowing past the
      end.
    - Values above the top edge likewise clamp to the last bucket.
    - Negative values clamp to the first bucket (index 0).

    This guarantees the result is always a valid index into a length-
    ``n_buckets`` list, so callers such as ``histogram_summary`` never raise
    an ``IndexError`` on out-of-range inputs.
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
