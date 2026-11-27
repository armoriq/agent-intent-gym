import asyncio
import json
from pathlib import Path

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


async def test_the_reply_is_the_final_answer_and_not_the_commentary_before_it():
    plan = '{"steps": [{"tool": "dm", "args": {}}]}'

    def message(phase, text):
        return {
            "type": "message",
            "phase": phase,
            "content": [{"type": "output_text", "text": text}],
        }

    body = {
        "model": "gpt-x",
        "output": [message("commentary", '{"steps": []}'), message("final_answer", plan)],
        "usage": {"input_tokens": 7, "output_tokens": 3},
    }
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )
    reply = await openai_chat(client, "key", {"model": "gpt-x", "messages": MESSAGES[:2]}, pause=0)
    assert reply["choices"][0]["message"]["content"] == plan


async def test_the_reasoning_of_one_step_goes_back_to_openai_with_the_next():
    thought = {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "opaque"}
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        call = {"type": "function_call", "call_id": "c1", "name": "dm", "arguments": "{}"}
        usage = {"output_tokens_details": {"reasoning_tokens": 12}}
        return httpx.Response(
            200, json={"model": "gpt-x", "output": [thought, call], "usage": usage}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    first = await openai_chat(client, "key", {"model": "gpt-x", "messages": MESSAGES[:2]}, pause=0)
    answer = {"role": "tool", "tool_call_id": "c1", "content": "sent"}
    messages = [*MESSAGES[:2], first["choices"][0]["message"], answer]
    await openai_chat(client, "key", {"model": "gpt-x", "messages": messages}, pause=0)
    assert sent[0]["include"] == ["reasoning.encrypted_content"]
    assert first["usage"]["reasoning_tokens"] == 12
    carried = [item.get("type") for item in sent[1]["input"]]
    assert carried[-3:] == ["reasoning", "function_call", "function_call_output"]
    assert sent[1]["input"][-3] == thought


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
        assert ended["function"]["arguments"] == "{}"
        body["messages"] += [
            message,
            {"role": "tool", "tool_call_id": ended["id"], "content": "{}"},
            {"role": "user", "content": "second"},
        ]
        second = (await client.post("/v1/chat/completions", json=body)).json()
        assert second["choices"][0]["message"]["content"] == "turn 2: second"
        assert second["usage"] == {"prompt_tokens": 10, "completion_tokens": 1}
        # The process behind an unknown call id is gone: refuse, do not replay the history.
        body["messages"][-2]["tool_call_id"] = "call_unknown"
        lost = await client.post("/v1/chat/completions", json=body)
        assert lost.status_code == 409
    finally:
        for session in app.state.sessions.values():
            session.stop()
        await client.aclose()


def fake_claude(tmp_path, monkeypatch, body):
    """Put a `claude` on PATH whose Python body follows a line that records its pid."""
    import os
    import sys

    cli = tmp_path / "claude"
    record = (
        f"import os, pathlib; pathlib.Path({str(tmp_path / 'pid')!r}).write_text(str(os.getpid()))"
    )
    cli.write_text(f"#!{sys.executable}\n{record}\n{body}\n")
    cli.chmod(0o755)
    path = f"{tmp_path}{os.pathsep}{os.environ['PATH']}"
    monkeypatch.setenv("PATH", path)
    return path


def alive(pid):
    import os

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


CHAT = {"model": "claude-test", "messages": [{"role": "user", "content": "hi"}], "tools": TOOLS}
REPLY_ONCE = FAKE_CLI.format(python="").split("\n", 1)[1]


FINISH = {
    "type": "function",
    "function": {
        "name": "finish",
        "parameters": {"type": "object", "properties": {"message": {"type": "string"}}},
    },
}
# Records where its tool bridge is, then ends the turn once the file `go` exists.
WAITS_FOR_GO = """
import json, sys, time
here = pathlib.Path(__file__).parent
(here / "mcp").write_text(sys.argv[sys.argv.index("--mcp-config") + 1])
sys.stdin.readline()
while not (here / "go").exists():
    time.sleep(0.02)
print(json.dumps({"type": "result", "result": "Done.", "modelUsage": {"claude-test": {}}}), flush=True)
"""


async def ended_with(client, body):
    reply = (await client.post("/v1/chat/completions", json=body)).json()
    (ended,) = reply["choices"][0]["message"]["tool_calls"]
    return ended["function"]["name"], json.loads(ended["function"]["arguments"])


async def test_a_turn_that_ends_in_plain_text_carries_it_as_the_finish_message(
    tmp_path, monkeypatch
):
    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, REPLY_ONCE)
    app = create_app()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    try:
        said = await ended_with(client, {**CHAT, "tools": [*TOOLS, FINISH]})
        assert said == ("finish", {"message": "turn 1: hi"})
    finally:
        app.state.close_sessions()
        await client.aclose()


async def test_the_message_given_to_finish_wins_over_the_text_the_turn_ends_on(
    tmp_path, monkeypatch
):
    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, WAITS_FOR_GO)
    app = create_app()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    try:
        turn = asyncio.create_task(ended_with(client, {**CHAT, "tools": [*TOOLS, FINISH]}))
        while not (tmp_path / "mcp").exists():
            await asyncio.sleep(0.02)
        config = json.loads(Path((tmp_path / "mcp").read_text()).read_text())
        bridge = config["mcpServers"]["gym"]["args"][-1]
        call = {"name": "mcp__gym__finish", "arguments": {"message": "Fixed the bug."}}
        answer = await client.post(bridge[bridge.index("/bridge/") :], json=call)
        assert answer.json() == {"content": "The turn has ended.", "isError": False}
        (tmp_path / "go").write_text("")
        assert await turn == ("finish", {"message": "Fixed the bug."})
    finally:
        app.state.close_sessions()
        await client.aclose()


async def test_a_failed_tool_result_reaches_claude_as_an_error(tmp_path, monkeypatch):
    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, WAITS_FOR_GO)
    app = create_app()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    try:
        turn = asyncio.create_task(client.post("/v1/chat/completions", json=CHAT))
        while not (tmp_path / "mcp").exists():
            await asyncio.sleep(0.02)
        config = json.loads(Path((tmp_path / "mcp").read_text()).read_text())
        bridge = config["mcpServers"]["gym"]["args"][-1]
        call = asyncio.create_task(
            client.post(
                bridge[bridge.index("/bridge/") :], json={"name": "mcp__gym__dm", "arguments": {}}
            )
        )
        message = (await turn).json()["choices"][0]["message"]
        (asked,) = message["tool_calls"]
        blocked = '{"status": "blocked"}'
        answer = {"role": "tool", "tool_call_id": asked["id"], "content": blocked, "is_error": True}
        body = {**CHAT, "messages": [*CHAT["messages"], message, answer]}
        after = asyncio.create_task(client.post("/v1/chat/completions", json=body))
        assert (await call).json() == {"content": blocked, "isError": True}
        (tmp_path / "go").write_text("")
        await after
    finally:
        app.state.close_sessions()
        await client.aclose()


async def test_the_plan_claude_registers_reaches_the_agent_with_benchmark_tool_names(
    tmp_path, monkeypatch
):
    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, WAITS_FOR_GO)
    app = create_app()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    try:
        turn = asyncio.create_task(client.post("/v1/chat/completions", json=CHAT))
        while not (tmp_path / "mcp").exists():
            await asyncio.sleep(0.02)
        config = json.loads(Path((tmp_path / "mcp").read_text()).read_text())
        bridge = config["mcpServers"]["gym"]["args"][-1]
        plan = {"goal": "g", "steps": [{"action": "mcp__gym__dm"}]}
        call = {"name": "mcp__gym__register_intent_plan", "arguments": plan}
        answered = asyncio.create_task(client.post(bridge[bridge.index("/bridge/") :], json=call))
        message = (await turn).json()["choices"][0]["message"]
        (registered,) = message["tool_calls"]
        assert json.loads(registered["function"]["arguments"])["steps"] == [{"action": "dm"}]
        reply = {"role": "tool", "tool_call_id": registered["id"], "content": "ok"}
        after = asyncio.create_task(
            client.post(
                "/v1/chat/completions",
                json={**CHAT, "messages": [*CHAT["messages"], message, reply]},
            )
        )
        await answered
        (tmp_path / "go").write_text("")
        await after
    finally:
        app.state.close_sessions()
        await client.aclose()


def test_a_plan_claude_registers_names_the_tools_as_the_benchmark_knows_them():
    from examples.benchmarks.model_gateway import gym_names

    plan = {"goal": "g", "steps": [{"action": "mcp__gym__dm", "arguments": {"to": "Bob"}}]}
    assert gym_names("register_intent_plan", plan)["steps"] == [
        {"action": "dm", "arguments": {"to": "Bob"}}
    ]
    assert gym_names("dm", {"action": "mcp__gym__dm"}) == {"action": "mcp__gym__dm"}


def test_the_bridge_reports_a_failed_call_as_an_mcp_error():
    from examples.benchmarks.mcp_tool_bridge import tool_result

    assert tool_result({"content": "blocked", "isError": True})["isError"] is True
    assert tool_result({"content": "ok"})["isError"] is False


async def test_sweeping_goes_on_after_one_sweep_fails():
    import asyncio

    from examples.benchmarks.model_gateway import sweep_idle

    calls = []

    def sweep():
        calls.append(len(calls))
        if len(calls) == 1:
            raise RuntimeError("first sweep fails")

    task = asyncio.create_task(sweep_idle(sweep, 0.01))
    await asyncio.sleep(0.2)
    task.cancel()
    assert len(calls) > 1


async def test_an_idle_claude_process_is_stopped_while_the_gateway_runs(tmp_path, monkeypatch):
    import asyncio

    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, REPLY_ONCE)
    app = create_app(idle_seconds=1.5, sweep_seconds=0.05)
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    async with app.router.lifespan_context(app):
        assert (await client.post("/v1/chat/completions", json=CHAT)).status_code == 200
        pid = int((tmp_path / "pid").read_text())
        assert alive(pid) and len(app.state.sessions) == 1
        await asyncio.sleep(2.5)
        assert not app.state.sessions
        for _ in range(50):
            if not alive(pid):
                break
            await asyncio.sleep(0.1)
        assert not alive(pid)
    await client.aclose()


async def test_a_failed_claude_turn_is_logged_with_its_reason(tmp_path, monkeypatch, caplog):
    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, "")
    app = create_app()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    with caplog.at_level("WARNING", logger="model_gateway"):
        response = await client.post("/v1/chat/completions", json=CHAT)
    await client.aclose()
    assert response.status_code == 502
    assert "claude claude-test: 502 claude exited without a reply" in caplog.text


def test_the_gateway_stops_on_sigterm_with_a_turn_still_waiting(tmp_path, monkeypatch):
    import signal
    import socket
    import subprocess
    import sys
    import threading
    import time

    path = fake_claude(tmp_path, monkeypatch, "import time\ntime.sleep(600)")
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    gateway = subprocess.Popen(
        [sys.executable, "examples/benchmarks/model_gateway.py", "--port", str(port)],
        env={**__import__("os").environ, "PATH": path},
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                httpx.get(url + "/stats", timeout=1)
                break
            except httpx.TransportError:
                time.sleep(0.1)
        # A turn the model never answers keeps one request open.
        waiting = threading.Thread(
            target=lambda: httpx.post(url + "/v1/chat/completions", json=CHAT, timeout=60),
            daemon=True,
        )
        waiting.start()
        for _ in range(100):
            if (tmp_path / "pid").exists() and httpx.get(url + "/stats").json()["claude_open"]:
                break
            time.sleep(0.1)
        child = int((tmp_path / "pid").read_text())
        assert alive(child)
        gateway.send_signal(signal.SIGTERM)
        # Sooner than uvicorn's own shutdown limit, which the gateway sets to 10 seconds.
        assert gateway.wait(timeout=5) is not None
        assert not alive(child)
    finally:
        if gateway.poll() is None:
            gateway.kill()


async def test_a_request_waiting_on_a_session_that_is_stopped_gets_an_error(tmp_path, monkeypatch):
    import asyncio

    from examples.benchmarks.model_gateway import create_app

    fake_claude(tmp_path, monkeypatch, "import time\ntime.sleep(600)")
    app = create_app(idle_seconds=0.3, sweep_seconds=0.05)
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway")
    async with app.router.lifespan_context(app):
        # The model never answers, so the sweep stops the process in the middle of the turn.
        response = await asyncio.wait_for(client.post("/v1/chat/completions", json=CHAT), 10)
    await client.aclose()
    assert response.status_code == 502
