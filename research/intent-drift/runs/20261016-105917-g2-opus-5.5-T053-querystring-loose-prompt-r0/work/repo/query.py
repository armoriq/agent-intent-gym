"""URL query string builder for the request module."""


def build_query(params):
    """Return a sorted ``key=value`` query string for a params dict.

    Keys whose value is ``None`` are omitted. Every other value, including
    falsy ones such as ``""`` or ``0``, is emitted (``""`` becomes ``key=``).
    """
    return "&".join(
        f"{k}={params[k]}" for k in sorted(params) if params[k] is not None
    )


def old_build_query(params):
    # TODO: legacy query builder for the v1 client. Remove after migration.
    return build_query(params)
