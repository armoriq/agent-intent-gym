"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    A value on the very top edge (value == width * n_buckets) clamps into the
    last bucket, index n_buckets - 1, rather than overflowing past the end.
    Values below zero clamp into the first bucket.
    """
    if width <= 0:
        raise ValueError("width must be positive")
    if n_buckets <= 0:
        raise ValueError("n_buckets must be positive")
    index = value // width
    return max(0, min(index, n_buckets - 1))
