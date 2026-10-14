from __future__ import annotations

import base64
import dataclasses
import enum
import hashlib
import importlib
import inspect
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def load_symbol(reference: str):
    module, separator, name = reference.partition(":")
    if not separator or not module or not name:
        raise ValueError("Use module:callable for factories and action mappers")
    return getattr(importlib.import_module(module), name)


def json_native(value: Any) -> Any:
    """Explicit reversible encodings for common native payloads; never silently stringify scores."""
    if value is None or isinstance(value, (str, bool, int, float)):
        json.dumps(value, allow_nan=False)
        return value
    if isinstance(value, Mapping):
        if not all(isinstance(k, str) for k in value):
            raise TypeError("Native artifact mappings require string keys")
        return {k: json_native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_native(v) for v in value]
    if isinstance(value, bytes):
        return {"__type__": "bytes", "base64": base64.b64encode(value).decode()}
    if isinstance(value, enum.Enum):
        return json_native(value.value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "model_dump"):
        return json_native(value.model_dump(mode="json"))
    if dataclasses.is_dataclass(value):
        return json_native(dataclasses.asdict(value))
    if type(value).__module__.startswith("numpy"):
        if hasattr(value, "shape") and value.shape:
            return {
                "__type__": "ndarray",
                "dtype": str(value.dtype),
                "shape": list(value.shape),
                "data": json_native(value.tolist()),
            }
        return json_native(value.item())
    raise TypeError(f"Unsupported native artifact type: {type(value).__name__}")


def source_identity(reference: str) -> dict:
    symbol = load_symbol(reference)
    return {"reference": reference, **object_identity(symbol)}


def object_identity(symbol) -> dict:
    try:
        source = inspect.getsourcefile(symbol)
    except TypeError:
        source = None
    identity = {
        "module": symbol.__module__,
        "qualname": symbol.__qualname__,
        "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest() if source else None,
    }
    if source:
        for parent in Path(source).resolve().parents:
            if (parent / ".git").exists():

                def git(*args, parent=parent):
                    return subprocess.run(
                        ["git", "-C", str(parent), *args],
                        capture_output=True,
                        text=True,
                        check=True,
                    ).stdout.strip()

                try:
                    identity["installed_revision"] = git("rev-parse", "HEAD")
                    identity["checkout_dirty"] = bool(git("status", "--porcelain"))
                except (OSError, subprocess.CalledProcessError):
                    identity["checkout_dirty"] = None
                    identity["git_metadata_status"] = "unavailable; source file hash retained"
                break
    return identity
