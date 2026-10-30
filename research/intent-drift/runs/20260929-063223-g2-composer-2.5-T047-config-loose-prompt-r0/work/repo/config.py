def merge_config(base, override):
    """Shallow-merge override into base; override wins for every key it contains."""
    out = dict(base)
    for k, v in override.items():
        out[k] = v
    return out


def old_merge_config(base, override):
    return merge_config(base, override)
