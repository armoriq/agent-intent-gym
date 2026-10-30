"""URL query string builder for the request module."""


def build_query(params):
    """Return a sorted ``key=value`` query string for a params dict."""
    parts = []
    for k in sorted(params):
        v = params[k]
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return "&".join(parts)


def old_build_query(params):
    # TODO: legacy query builder for the v1 client. Remove after migration.
    return build_query(params)
