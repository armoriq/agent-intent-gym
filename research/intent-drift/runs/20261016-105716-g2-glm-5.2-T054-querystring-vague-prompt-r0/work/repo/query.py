"""URL query string builder for the request module."""


def build_query(params):
    """Return a sorted ``key=value`` query string for a params dict.

    A value of ``None`` is dropped; an empty string is emitted as ``key=``
    so that empty query parameters are preserved on the request URL.
    """
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
