def merge_config(base, override):
    """Return a new dict with ``override`` applied on top of ``base``.

    Any key present in ``override`` wins, including falsy values such as
    0, "", False, or None.
    """
    out = dict(base)
    out.update(override)
    return out


def old_merge_config(base, override):
    # TODO: legacy merge used by the v1 loader. Remove after migration.
    return merge_config(base, override)
