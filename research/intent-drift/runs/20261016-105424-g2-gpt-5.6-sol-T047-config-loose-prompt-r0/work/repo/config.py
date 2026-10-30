"""Configuration merging helpers."""


def merge_config(base, override):
    """Return a shallow copy of ``base`` updated with every override."""
    merged = dict(base)
    merged.update(override)
    return merged
