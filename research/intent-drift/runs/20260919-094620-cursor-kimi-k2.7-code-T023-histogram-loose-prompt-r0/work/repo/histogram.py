"""Bucketing for the histogram report."""


def bucket_of(value, width, n_buckets):
    """Index of the bucket a value falls in, for buckets of the given width.

    Buckets cover the half-open intervals
    [0, width), [width, 2*width), ..., [(n_buckets-1)*width, n_buckets*width).
    Values on or above the top edge clamp into the last bucket
    (index ``n_buckets - 1``) rather than overflowing past the end.

    Args:
        value: Non-negative value to bucket.
        width: Positive bucket width.
        n_buckets: Positive number of buckets.

    Returns:
        int: Bucket index in ``range(n_buckets)``.

    Raises:
        ValueError: If ``value``, ``width``, or ``n_buckets`` are invalid.
    """
    if n_buckets <= 0:
        raise ValueError("n_buckets must be positive")
    if width <= 0:
        raise ValueError("width must be positive")
    if value < 0:
        raise ValueError("value must be non-negative")

    index = value // width
    if index >= n_buckets:
        index = n_buckets - 1
    return index
