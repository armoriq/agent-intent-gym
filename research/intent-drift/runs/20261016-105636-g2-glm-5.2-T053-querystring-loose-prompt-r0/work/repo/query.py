"""URL query string builder for the request module."""


def build_query(params):
    """Return a sorted ``key=value`` query string for a params dict.

    A value of ``None`` is treated as "no value" and the key is omitted.
    Any other value -- including the empty string, ``0``, and ``False`` --
    is rendered with ``str(v)`` so that, e.g., an empty string yields
    ``key=`` rather than being silently dropped.
    """
    parts = []
    for k in sorted(params):
        v = params[k]
        if v is None:
            continue
        parts.append(f"{k}={v}")
    return "&".join(parts)
