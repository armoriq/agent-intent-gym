"""Load local secrets without copying them into benchmark configurations."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from .models import AdapterConfig


def load_environment(path: str | Path | None = None) -> None:
    # Deliberately do not search parent/home directories for unrelated credentials.
    load_dotenv(Path(path) if path else Path.cwd() / ".env", override=False)


def resolve_adapter(config: AdapterConfig) -> AdapterConfig:
    load_environment()
    data = config.model_dump()
    for field in ("endpoint", "model"):
        name = data.get(field + "_env")
        if name and os.environ.get(name):
            data[field] = os.environ[name]
    # Revalidate environment URLs too: credentials must stay out of URL strings.
    return AdapterConfig.model_validate(data)


def model_identity(config: AdapterConfig) -> dict:
    resolved = resolve_adapter(config)
    protocol = resolved.options.get("protocol")
    if not protocol and resolved.kind == "openai":
        protocol = "chat-completions"
    elif not protocol and resolved.factory == "examples.benchmarks.ollama_agent:create_agent":
        protocol = os.environ.get("MODEL_PROTOCOL", "ollama")
    return {
        "kind": resolved.kind,
        "model": resolved.model,
        "endpoint": resolved.endpoint,
        "protocol": protocol,
    }


def protection_identity(config: AdapterConfig | None) -> dict | None:
    if not config:
        return None
    load_environment()
    identity = {"kind": config.kind}
    if config.kind == "armoriq":
        identity["agent_id"] = armoriq_agent_id(config)
        identity["tool_name_mode"] = config.options.get("tool_name_mode", "mcp")
        identity["tool_catalog_sha256"] = config.options.get("tool_catalog_sha256")
        identity["sdk_mode"] = (
            config.options.get("sdk_mode") or os.environ.get("ARMORIQ_SDK_MODE") or "sdk"
        )
        # Unset endpoints intentionally leave default selection to the installed SDK.
        for option in ("iap_endpoint", "backend_endpoint", "proxy_endpoint"):
            endpoint = config.options.get(option) or os.environ.get("ARMORIQ_" + option.upper())
            if endpoint:
                AdapterConfig(kind="settings", endpoint=endpoint)
            identity[option] = endpoint
    return identity


def armoriq_agent_id(config: AdapterConfig) -> str | None:
    load_environment()
    return (
        config.options.get("agent_id")
        or os.environ.get(config.options.get("agent_id_env", "ARMORIQ_AGENT_ID"))
        or os.environ.get("AGENT_ID")
        or None
    )


def require_armoriq_credentials(config: AdapterConfig) -> None:
    load_environment()
    missing = []
    key = config.api_key_env or "ARMORIQ_API_KEY"
    email = config.options.get("user_email_env", "ARMORIQ_USER_EMAIL")
    if not os.environ.get(key):
        missing.append(key)
    if not config.options.get("user_email") and not os.environ.get(email):
        missing.append(email)
    if missing:
        raise ValueError("Set " + ", ".join(missing) + " in .env or the process environment")
