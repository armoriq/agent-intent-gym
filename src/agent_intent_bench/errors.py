import os

from .models import RunConfig


def safe_error(error: Exception, config: RunConfig | None = None) -> str:
    message = f"{type(error).__name__}: {error}"
    names = {
        "ARMORIQ_API_KEY",
        "ARMORIQ_ACCESS_TOKEN",
        "OPENAI_API_KEY",
        "MODEL_API_KEY",
        "ANTHROPIC_API_KEY",
        "ARMORIQ_USER_EMAIL",
        "INTENTBENCH_API_TOKEN",
        getattr(getattr(config, "agent", None), "api_key_env", None),
        getattr(getattr(config, "guard", None), "api_key_env", None),
    }
    for name in names:
        value = os.environ.get(name) if name else None
        if value:
            message = message.replace(value, "[REDACTED]")
    return message
