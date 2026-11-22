import httpx
import pytest
from fastapi import HTTPException

from examples.benchmarks.model_gateway import (
    final_reply,
    openai_chat,
    responses_request,
    tokens,
    transcript,
)

MESSAGES = [
    {"role": "system", "content": "Use the tools."},
    {"role": "user", "content": "Send Bob a message."},
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "dm", "arguments": "{}"}}
        ],
    },
    {"role": "tool", "tool_call_id": "call_1", "content": '{"status": "ok"}'},
]
TOOLS = [{"type": "function", "function": {"name": "dm", "parameters": {"type": "object"}}}]


def test_chat_request_becomes_a_responses_request_with_paired_tool_calls():
    request = responses_request(
        {"model": "gpt-x", "messages": MESSAGES, "tools": TOOLS, "temperature": 0, "seed": 1}
    )
    assert [item.get("type", item.get("role")) for item in request["input"]] == [
        "developer",
        "user",
        "function_call",
        "function_call_output",
    ]
    assert request["input"][2]["call_id"] == request["input"][3]["call_id"] == "call_1"
    assert request["tools"] == [
        {"type": "function", "name": "dm", "parameters": {"type": "object"}}
    ]
    assert request["parallel_tool_calls"] is False
    assert "temperature" not in request and "seed" not in request


def test_reasoning_is_requested_only_from_models_that_accept_it():
    def request(model):
        return responses_request({"model": model, "messages": MESSAGES})

    assert request("gpt-6-luna")["reasoning"] == {"effort": "medium"}
    assert "reasoning" not in request("gpt-4o-mini")


def test_cli_prompt_is_the_bare_request_when_nothing_else_was_said():
    assert transcript(MESSAGES[:2]) == "Send Bob a message."
    assert "[tool result call_1]" in transcript(MESSAGES)


async def test_openai_call_is_retried_after_a_server_error():
    replies = [
        httpx.Response(502, json={"error": {"code": "bad_gateway", "message": "upstream"}}),
        httpx.Response(
            200,
            json={
                "model": "gpt-x",
                "output": [
                    {"type": "function_call", "call_id": "c1", "name": "dm", "arguments": "{}"}
                ],
                "usage": {"input_tokens": 7, "output_tokens": 3},
            },
        ),
    ]
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: replies.pop(0)))
    reply = await openai_chat(client, "key", {"model": "gpt-x", "messages": MESSAGES[:2]}, pause=0)
    assert reply["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "dm"
    assert not replies


async def test_openai_client_error_is_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(400, json={"error": {"code": "invalid", "message": "bad input"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(HTTPException, match="bad input"):
        await openai_chat(client, "key", {"model": "gpt-x", "messages": MESSAGES[:2]}, pause=0)
    assert len(calls) == 1


def test_a_claude_turn_answered_by_another_model_is_refused():
    closing = {
        "result": "done",
        "modelUsage": {
            "claude-a": {"inputTokens": 5, "cacheReadInputTokens": 20, "outputTokens": 9}
        },
    }
    assert tokens("claude-a", final_reply("claude-a", closing)) == {
        "prompt_tokens": 25,
        "completion_tokens": 9,
    }
    with pytest.raises(HTTPException, match="answered with"):
        final_reply("claude-b", closing)
    with pytest.raises(HTTPException, match="without a reply"):
        final_reply("claude-a", None)


FAKE_CLI = """#!{python}
import json, sys
turn = 0
for line in sys.stdin:
    turn += 1
    text = json.loads(line)["message"]["content"][0]["text"]
    usage = {{"claude-test": {{"inputTokens": 10 * turn, "outputTokens": turn}}}}
    print(json.dumps({{"type": "result", "result": f"turn {{turn}}: {{text}}", "modelUsage": usage}}), flush=True)
"""


async def test_a_second_user_turn_goes_to_the_same_claude_process(tmp_path, monkeypatch):
    import os
    import sys

    from examples.benchmarks.model_gateway import create_app

    cli = tmp_path / "claude"
    cli.write_text(FAKE_CLI.format(python=sys.executable))
    cli.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    app = create_app()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    body = {
        "model": "claude-test",
        "messages": [{"role": "user", "content": "first"}],
        "tools": TOOLS,
    }
    try:
        first = (await client.post("/v1/chat/completions", json=body)).json()
        message = first["choices"][0]["message"]
        (ended,) = message["tool_calls"]
        assert ended["function"]["name"] == "finish" and message["content"] == "turn 1: first"
        body["messages"] += [
            message,
            {"role": "tool", "tool_call_id": ended["id"], "content": "{}"},
            {"role": "user", "content": "second"},
        ]
        second = (await client.post("/v1/chat/completions", json=body)).json()
        assert second["choices"][0]["message"]["content"] == "turn 2: second"
        assert second["usage"] == {"prompt_tokens": 10, "completion_tokens": 1}
    finally:
        for session in app.state.sessions.values():
            session.stop()
        await client.aclose()
