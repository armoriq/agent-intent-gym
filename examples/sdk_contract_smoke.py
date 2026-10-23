"""Exercise the actual SDK session interface against an offline mock transport.

uv run --with-editable ../armoriq-sdk-customer python examples/sdk_contract_smoke.py
Explicit fixture credentials and mock endpoints; no request reaches an ArmorIQ server or MCP tool.
"""

import asyncio
import json
import os
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from agent_intent_bench.adapters import ArmorIQGuard
from agent_intent_bench.models import Action, AdapterConfig, Intent, ToolCall


async def main():
    os.environ["INTENTBENCH_SDK_TEST_KEY"] = "ak_test_offline_contract"
    # Constructor authentication must also stay offline, before HTTP transport
    # replacement. The real session/enforcement code is exercised below.
    from armoriq_sdk import ArmorIQClient

    authentication = (
        patch("armoriq_sdk.ArmorIQClient._validate_api_key", return_value=None)
        if hasattr(ArmorIQClient, "_validate_api_key")
        else nullcontext()
    )
    with authentication:
        guard = ArmorIQGuard(
            AdapterConfig(
                kind="armoriq",
                api_key_env="INTENTBENCH_SDK_TEST_KEY",
                options={
                    "user_email": "tester@example.test",
                    "sdk_mode": "sdk",
                    "iap_endpoint": "http://sdk.test",
                    "backend_endpoint": "http://sdk.test",
                    "proxy_endpoint": "http://sdk.test",
                },
            )
        )
    requests = []

    def transport(request):
        assert request.url.path == "/iap/sdk/enforce"
        body = json.loads(request.content)
        assert body["user_email"] == "tester@example.test"
        requests.append(body)
        allowed = body["arguments"].get("beneficiary") == "ACME"
        return httpx.Response(
            200,
            json={
                "allowed": allowed,
                "enforcementAction": "allow" if allowed else "block",
                "reason": "Offline transport fixture",
            },
        )

    guard.client.http_client.close()
    guard.client.http_client = httpx.Client(transport=httpx.MockTransport(transport))
    guard.client.capture_plan = lambda *args, **kwargs: SimpleNamespace()
    guard.client.get_intent_token = lambda *args, **kwargs: SimpleNamespace(
        is_expired=False,
        raw_token={"fixture": True},
        policy_snapshot=[],
        policy_validation={},
        plan_id="offline-plan",
        signed=lambda: {"plan_id": "offline-plan"},
    )
    context = {"intent": Intent(id="native-test", objective="Pay Acme").model_dump()}
    await guard.evaluate(
        Action(kind="plan", plan=[ToolCall(tool="payments__commit", args={"beneficiary": "ACME"})]),
        context,
    )
    assert (
        await guard.evaluate(Action(tool="payments__commit", args={"beneficiary": "ACME"}), context)
    ).action == "allow"
    assert (
        await guard.evaluate(
            Action(tool="payments__commit", args={"beneficiary": "ATTACKER"}), context
        )
    ).action == "block"
    await guard.aclose()
    assert len(requests) == 2
    print(
        "Native SDK start_plan/check interface verified against offline transport; no real backend tested."
    )


if __name__ == "__main__":
    asyncio.run(main())
