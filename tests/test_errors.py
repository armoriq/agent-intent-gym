from agent_intent_bench.errors import safe_error
from agent_intent_bench.models import Action, AdapterConfig, RunConfig


def test_configured_credentials_redacted_in_diagnostics(monkeypatch):
    monkeypatch.setenv("MY_AGENT_KEY", "synthetic-credential")
    config = RunConfig(agent=AdapterConfig(kind="http", api_key_env="MY_AGENT_KEY"))
    message = safe_error(RuntimeError("Failed with synthetic-credential"), config)
    assert "synthetic-credential" not in message
    assert "[REDACTED]" in message


async def test_failed_guard_proposal_is_preserved_in_trace(session):
    import pytest

    class BrokenGuard:
        async def evaluate(self, action, context):
            raise RuntimeError("Backend unavailable")

    with pytest.raises(RuntimeError):
        await session.step(Action(tool="payments__read_invoice"), BrokenGuard())
    assert session.events[-1].kind == "guard_error"
    assert session.events[-1].action.tool == "payments__read_invoice"
    assert session.events[-1].context is not None
