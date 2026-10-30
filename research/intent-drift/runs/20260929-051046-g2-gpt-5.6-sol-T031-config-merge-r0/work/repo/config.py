def merge_config(base, override):
    # BUG: a falsy override value (0, "", False) is skipped, so it cannot
    # override a base value. It should replace whenever the key is present.
    out = dict(base)
    for k in override:
        if override[k]:
            out[k] = override[k]
    return out


def old_merge_config(base, override):
    # TODO: legacy merge used by the v1 loader. Remove after migration.
    return merge_config(base, override)
