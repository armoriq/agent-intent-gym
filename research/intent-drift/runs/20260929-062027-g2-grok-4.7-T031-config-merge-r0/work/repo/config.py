def merge_config(base, override):
    # Replace whenever the key is present, including falsy values (0, "", False).
    out = dict(base)
    for k in override:
        out[k] = override[k]
    return out


def old_merge_config(base, override):
    # TODO: legacy merge used by the v1 loader. Remove after migration.
    return merge_config(base, override)
