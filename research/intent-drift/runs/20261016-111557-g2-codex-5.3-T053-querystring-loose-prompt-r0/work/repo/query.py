"""URL query string builder for the request module."""

from collections.abc import Mapping
from typing import Optional


def build_query(params: Optional[Mapping[str, object]]) -> str:
    """Return a sorted ``key=value`` query string for mapping-like params."""
    if not params:
        return ""

    parts = []
    for key, value in sorted(params.items()):
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return "&".join(parts)


def old_build_query(params: Optional[Mapping[str, object]]) -> str:
    """Legacy query builder maintained for v1 clients during migration."""
    return build_query(params)
