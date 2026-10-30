"""URL query string builder for the request module."""


def build_query(params):
    """Return a sorted ``key=value`` query string for a params dict.

    Keys with a value of ``None`` are omitted; other values — including
    empty strings — are emitted as ``key=<value>``.
    """
    parts = []
    for k in sorted(params):
        v = params[k]
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return "&".join(parts)
