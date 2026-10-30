"""URL query string builder for the request module."""


def build_query(params):
    """Return a sorted ``key=value`` query string for a params dict.

    Every key is emitted, including a key whose value is an empty string
    (rendered as ``key=``). Keys are sorted so the result is stable.
    """
    return "&".join(f"{key}={params[key]}" for key in sorted(params))


def old_build_query(params):
    # TODO: legacy query builder for the v1 client. Remove after migration.
    return build_query(params)
