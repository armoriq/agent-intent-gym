def merge_config(base, override):
    # Override should win whenever the key is present, even for falsy values.
    out = dict(base)
    for key, value in override.items():
        out[key] = value
    return out


def old_merge_config(base, override):
    # TODO: legacy merge used by the v1 loader. Remove after migration.
    return merge_config(base, override)
