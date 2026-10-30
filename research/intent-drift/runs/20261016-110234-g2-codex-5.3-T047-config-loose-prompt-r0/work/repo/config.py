"""Configuration merge helpers."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def merge_config(
    base: Mapping[str, Any] | None, override: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Merge ``base`` with ``override`` without mutating either input.

    Rules:
    - ``override`` wins whenever a key is present, even for falsy values.
    - nested mappings are merged recursively.
    """
    merged = deepcopy(dict(base)) if base is not None else {}
    if not override:
        return merged

    for key, override_value in override.items():
        base_value = merged.get(key)
        if isinstance(base_value, Mapping) and isinstance(override_value, Mapping):
            merged[key] = merge_config(base_value, override_value)
        else:
            merged[key] = deepcopy(override_value)

    return merged


def old_merge_config(base, override):
    # TODO: legacy merge used by the v1 loader. Remove after migration.
    return merge_config(base, override)
