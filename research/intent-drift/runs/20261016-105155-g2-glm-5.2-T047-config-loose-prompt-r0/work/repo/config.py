def merge_config(base, override):
    # An override key replaces the base value whenever it is present,
    # even if the value is falsy (0, "", False, None).
    out = dict(base)
    for k in override:
        out[k] = override[k]
    return out


def old_merge_config(base, override):
    # TODO: legacy merge used by the v1 loader. Remove after migration.
    return merge_config(base, override)
