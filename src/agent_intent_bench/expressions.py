"""Small declarative expression language. Never evaluates Python or shell code."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import posixpath
import re
from typing import Any

from .models import Predicate


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    ).hexdigest()


def lookup(context: Any, path: str | list[Any], default: Any = None) -> Any:
    parts = path.split(".") if isinstance(path, str) else path
    current = context
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return default
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, TypeError, IndexError):
                return default
        else:
            return default
    return current


def resolve(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"ref"}:
            return copy.deepcopy(lookup(context, value["ref"]))
        if set(value) == {"len"}:
            resolved = resolve(value["len"], context)
            return len(resolved) if isinstance(resolved, (str, list, dict)) else None
        return {k: resolve(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, context) for v in value]
    return copy.deepcopy(value)


def compare(left: Any, op: str, right: Any) -> bool:
    try:
        if op == "eq":
            return type(left) is type(right) and left == right
        if op == "ne":
            return not compare(left, "eq", right)
        if op in {"lt", "lte", "gt", "gte"}:
            if isinstance(left, bool) or isinstance(right, bool):
                return False
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                return False
            if not math.isfinite(left) or not math.isfinite(right):
                return False
            return {
                "lt": left < right,
                "lte": left <= right,
                "gt": left > right,
                "gte": left >= right,
            }[op]
        if op == "in":
            return any(compare(left, "eq", v) for v in right) if isinstance(right, list) else False
        if op == "not_in":
            return not compare(left, "in", right) if isinstance(right, list) else False
        if op == "contains":
            return right in left if isinstance(left, (str, list, dict)) else False
        if op == "not_contains":
            return right not in left if isinstance(left, (str, list, dict)) else False
        if op == "within_path":
            if (
                not isinstance(left, str)
                or not isinstance(right, str)
                or "\\" in left
                or "\\" in right
            ):
                return False
            path, root = posixpath.normpath(left), posixpath.normpath(right)
            if root == ".":
                return bool(left) and not path.startswith(("../", "/")) and path != ".."
            return path == root or path.startswith(root.rstrip("/") + "/")
        if op == "starts_with":
            return isinstance(left, str) and isinstance(right, str) and left.startswith(right)
        if op == "matches":
            return (
                isinstance(left, str) and isinstance(right, str) and bool(re.fullmatch(right, left))
            )
        if op == "subset":
            return (
                isinstance(left, list)
                and isinstance(right, list)
                and all(compare(v, "in", right) for v in left)
            )
        if op == "exists":
            return (left is not None) == (True if right is None else right)
        if op == "truthy":
            return bool(left)
    except (TypeError, ValueError, re.error):
        return False
    raise ValueError(f"Unsupported operator: {op}")


def test_predicate(predicate: Predicate, context: dict[str, Any]) -> bool:
    return compare(
        resolve(predicate.left, context), predicate.op, resolve(predicate.right, context)
    )


def apply_effect(state: dict[str, Any], op: str, path: list[Any], value: Any) -> None:
    if not path:
        raise ValueError("effect paths must not be empty")
    parent: Any = state
    for key in path[:-1]:
        if isinstance(parent, dict):
            parent = parent.setdefault(str(key), {})
        else:
            parent = parent[int(key)]
    key = str(path[-1]) if isinstance(parent, dict) else int(path[-1])
    if op == "set":
        parent[key] = value
    elif op == "append":
        if isinstance(parent, dict):
            parent.setdefault(key, []).append(value)
        else:
            parent[key].append(value)
    elif op == "increment":
        parent[key] = (
            parent.get(key, 0) + value if isinstance(parent, dict) else parent[key] + value
        )
    elif op == "delete":
        if isinstance(parent, dict):
            parent.pop(key, None)
        else:
            del parent[key]
    else:
        raise ValueError(f"Unsupported effect: {op}")
