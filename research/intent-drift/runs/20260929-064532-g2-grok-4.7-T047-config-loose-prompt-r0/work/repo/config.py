def merge_config(base, override):
    """Return a new mapping with every override key applied.

    A key present in ``override`` replaces the base value even when the
    override is falsy (``0``, ``""``, ``False``, ``None``).
    """
    merged = dict(base)
    merged.update(override)
    return merged


def old_merge_config(base, override):
    """Legacy alias for :func:`merge_config`."""
    return merge_config(base, override)
