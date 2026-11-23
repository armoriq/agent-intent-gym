"""Local chat-completions gateway so one agent adapter can drive every evaluated model.

`gpt-*` models go to the OpenAI Responses API with native function tools, because the
chat-completions endpoint refuses function tools on reasoning models.

`claude-*` models go to the `claude` CLI in print mode with its built-in tools, settings,
other MCP servers and slash commands switched off. One CLI process serves one episode,
across every user turn. The episode's tools reach the model as real tools through
`mcp_tool_bridge.py`; each call is handed to the benchmark and its result is returned to the
same process, so tool calls and history are native. Tool names carry the prefix `mcp__gym__`
on that route. A turn that ends with plain text reaches the adapter as a `finish` call, and
the process then waits for the next user message until it has been idle for IDLE_SECONDS.

Neither route accepts a temperature or a seed, so runs are repeated instead of seeded.
The OpenAI key is read from a file given on the command line and never logged.

    uv run --no-sync python -m examples.benchmarks.model_gateway --openai-key-file PATH
"""

import argparse
import asyncio
import json
import logging
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request

EFFORT = "medium"
# These OpenAI families reject the reasoning option.
NO_REASONING = ("gpt-4o", "gpt-4.1")
IDLE_SECONDS = 180
FINISH_SECONDS = 120
# Three attempts of OPENAI_SECONDS each, plus the pauses between them, fit inside the model
# runner's 300 second step limit, so a stalled call is retried instead of ending the episode.
OPENAI_ATTEMPTS = 3
OPENAI_SECONDS = 90
OPENAI_RETRYABLE = {429, 500, 502, 503, 504}
log = logging.getLogger("model_gateway")
BRIDGE = Path(__file__).with_name("mcp_tool_bridge.py")
PREFIX = "mcp__gym__"


def responses_request(body):
    """Chat-completions request -> OpenAI Responses request."""
    items = []
    for message in body["messages"]:
        role, content = message["role"], message.get("content") or ""
        if role == "system":
            items.append({"role": "developer", "content": content})
        elif role == "tool":
            items.append(
                {
                    "type": "function_call_output",
                    "call_id": message["tool_call_id"],
                    "output": content,
                }
            )
        else:
            if content:
                items.append({"role": role, "content": content})
            for call in message.get("tool_calls") or []:
                items.append(
                    {
                        "type": "function_call",
                        "call_id": call["id"],
                        "name": call["function"]["name"],
                        "arguments": call["function"]["arguments"],
                    }
                )
    request = {
        "model": body["model"],
        "input": items,
        "store": False,
    }
    if not body["model"].startswith(NO_REASONING):
        request["reasoning"] = {"effort": EFFORT}
    if body.get("tools"):
        request["tools"] = [{"type": "function", **tool["function"]} for tool in body["tools"]]
        request["parallel_tool_calls"] = False
    if (body.get("response_format") or {}).get("type") == "json_object":
        request["text"] = {"format": {"type": "json_object"}}
    return request


def completion(model, content, calls, usage=None):
    message = {"role": "assistant", "content": content or None}
    if calls:
        message["tool_calls"] = [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
            for call_id, name, arguments in calls
        ]
    return {
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
        "usage": usage or {"prompt_tokens": 0, "completion_tokens": 0},
    }


async def openai_chat(client, key, body, pause=2.0):
    request = responses_request(body)
    for attempt in range(1, OPENAI_ATTEMPTS + 1):
        try:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                json=request,
                headers={"Authorization": "Bearer " + key},
            )
        except httpx.TransportError as error:
            status, detail = None, type(error).__name__
        else:
            if response.status_code == 200:
                break
            error = response.json().get("error", {})
            status = response.status_code
            detail = f"{error.get('code')}: {error.get('message', '')}"
        log.warning("openai %s attempt %s: %s %s", body["model"], attempt, status, detail)
        if attempt == OPENAI_ATTEMPTS or (status and status not in OPENAI_RETRYABLE):
            raise HTTPException(502, f"OpenAI {status}: {detail}")
        await asyncio.sleep(pause * 2 ** (attempt - 1))
    data = response.json()
    if not data["model"].startswith(body["model"]):
        raise HTTPException(502, f"OpenAI answered with {data['model']}")
    text = "".join(
        part["text"]
        for item in data["output"]
        if item["type"] == "message"
        for part in item["content"]
        if part["type"] == "output_text"
    )
    calls = [
        (item["call_id"], item["name"], item["arguments"])
        for item in data["output"]
        if item["type"] == "function_call"
    ]
    usage = data.get("usage", {})
    return completion(
        data["model"],
        text,
        calls,
        {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        },
    )


def transcript(messages):
    """Flatten the conversation after the system prompt into the CLI's first prompt."""
    messages = [m for m in messages if m["role"] != "system"]
    if len(messages) == 1:
        return messages[0].get("content") or ""
    lines = []
    for message in messages:
        role, content = message["role"], message.get("content") or ""
        if role == "tool":
            lines.append(f"[tool result {message['tool_call_id']}]\n{content}")
            continue
        if content:
            lines.append(f"[{role}]\n{content}")
        for call in message.get("tool_calls") or []:
            function = call["function"]
            lines.append(
                f"[assistant called {function['name']} as {call['id']}]\n{function['arguments']}"
            )
    return "\n\n".join(lines)


def final_reply(model, event):
    """The event that closes one CLI turn, refused unless the requested model produced it."""
    if event is None:
        raise HTTPException(502, "claude exited without a reply")
    if event.get("is_error") or not isinstance(event.get("result"), str):
        raise HTTPException(502, f"claude returned no reply: {event.get('subtype')}")
    if model not in event.get("modelUsage", {}):
        raise HTTPException(502, f"claude answered with {sorted(event.get('modelUsage', {}))}")
    return event


def tokens(model, event):
    """Token totals of the requested model for the whole CLI session so far."""
    usage = event["modelUsage"][model]
    return {
        "prompt_tokens": sum(
            usage.get(k, 0)
            for k in ("inputTokens", "cacheCreationInputTokens", "cacheReadInputTokens")
        ),
        "completion_tokens": usage.get("outputTokens", 0),
    }


def user_line(text):
    message = {"role": "user", "content": [{"type": "text", "text": text}]}
    return (json.dumps({"type": "user", "message": message}) + "\n").encode()


class ClaudeSession:
    """One `claude -p` process for one episode: every user turn goes to the same process,
    and its tool calls are answered by the benchmark."""

    def __init__(self, model):
        self.id = uuid.uuid4().hex[:12]
        self.model = model
        self.events = asyncio.Queue()
        self.process = None
        self.reader = None
        self.counted = {"prompt_tokens": 0, "completion_tokens": 0}
        self.touched = time.monotonic()

    async def start(self, body, workdir, port):
        system = "\n\n".join(
            m.get("content") or "" for m in body["messages"] if m["role"] == "system"
        )
        command = [
            "claude",
            "-p",
            "--model",
            self.model,
            "--effort",
            EFFORT,
            "--system-prompt",
            system,
            "--tools",
            "",
            "--strict-mcp-config",
            "--setting-sources",
            "",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        if body.get("tools"):
            folder = Path(workdir)
            tools_file = folder / f"{self.id}-tools.json"
            tools_file.write_text(json.dumps([tool["function"] for tool in body["tools"]]))
            config = {
                "mcpServers": {
                    "gym": {
                        "command": sys.executable,
                        "args": [
                            str(BRIDGE),
                            str(tools_file),
                            f"http://127.0.0.1:{port}/bridge/{self.id}/call",
                        ],
                    }
                }
            }
            config_file = folder / f"{self.id}-mcp.json"
            config_file.write_text(json.dumps(config))
            command += ["--mcp-config", str(config_file), "--allowedTools", "mcp__gym"]
        else:
            command[command.index("--system-prompt") + 1] = (
                system + "\n\nReply with the JSON object only, with no code fence or other text."
            )
        self.process = await asyncio.create_subprocess_exec(
            *command,
            cwd=workdir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=64 * 1024 * 1024,
        )
        self.reader = asyncio.create_task(self.read())
        await self.send(transcript(body["messages"]))

    async def read(self):
        """Queue the event that closes each turn; None when the process ends."""
        while line := await self.process.stdout.readline():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "result":
                await self.events.put(("reply", event))
        await self.events.put(("reply", None))

    async def send(self, text):
        self.process.stdin.write(user_line(text))
        await self.process.stdin.drain()

    async def next_event(self):
        """The model's next tool call, or the reply that ends its turn."""
        kind, event = await self.events.get()
        self.touched = time.monotonic()
        return (kind, final_reply(self.model, event)) if kind == "reply" else (kind, event)

    def spent(self, event):
        """Tokens used since the last turn that was counted."""
        total = tokens(self.model, event)
        delta = {key: total[key] - self.counted[key] for key in total}
        self.counted = total
        return delta

    def stop(self):
        if self.process and self.process.returncode is None:
            self.process.kill()
        if self.reader:
            self.reader.cancel()


def create_app(openai_key=None, port=8791):
    # pending: a tool call waiting for its result. parked: a finished turn waiting for the
    # user's next message. Both are keyed by the call id handed to the agent adapter.
    sessions, pending, parked = {}, {}, {}

    async def sweep_idle():
        while True:
            await asyncio.sleep(30)
            sweep()

    @asynccontextmanager
    async def lifespan(app):
        sweeper = asyncio.create_task(sweep_idle())
        yield
        sweeper.cancel()
        for session in sessions.values():
            session.stop()

    app = FastAPI(lifespan=lifespan)
    app.state.sessions = sessions
    workdir = tempfile.mkdtemp(prefix="model-gateway-")
    client = httpx.AsyncClient(timeout=OPENAI_SECONDS)
    stats = {
        "claude_sessions": 0,
        "claude_turns": 0,
        "claude_stopped_mid_turn": 0,
        "claude_lost_sessions": 0,
    }

    def sweep():
        waiting = {id(s) for s in parked.values()}
        for session in list(sessions.values()):
            if time.monotonic() - session.touched <= IDLE_SECONDS:
                continue
            session.stop()
            sessions.pop(session.id, None)
            if id(session) not in waiting:
                stats["claude_stopped_mid_turn"] += 1
            for table in (pending, parked):
                for call_id, entry in list(table.items()):
                    if session in (entry if isinstance(entry, tuple) else (entry,)):
                        table.pop(call_id)
                        if isinstance(entry, tuple):
                            entry[1].cancel()

    async def end_of_turn(session, body, reply, call_id):
        """Hand the adapter a `finish` call it can answer when the user speaks again."""
        stats["claude_turns"] += 1
        parked[call_id] = session
        text = reply["result"].strip()
        return completion(body["model"], text, [(call_id, "finish", "{}")], session.spent(reply))

    async def claude_chat(body):
        sweep()
        trailing = []
        for message in reversed(body["messages"]):
            if message["role"] == "assistant":
                break
            trailing.insert(0, message)
        answered = [m["tool_call_id"] for m in trailing if m["role"] == "tool"]
        if any(call_id in pending for call_id in answered):
            session, future = pending.pop(next(c for c in answered if c in pending))
            future.set_result("\n\n".join(m.get("content") or "" for m in trailing))
        elif any(call_id in parked for call_id in answered):
            session = parked.pop(next(c for c in answered if c in parked))
            said = [m.get("content") or "" for m in trailing if m["role"] == "user"]
            if not said:
                raise HTTPException(400, "A finished turn needs a new user message")
            await session.send("\n\n".join(said))
        elif body.get("tools") and len(trailing) < len(body["messages"]):
            # A conversation that already has an assistant turn belongs to a process that
            # is gone (swept while idle, or the gateway restarted). Starting a new one would
            # replay its history as user text.
            stats["claude_lost_sessions"] += 1
            raise HTTPException(409, "The Claude session for this conversation has ended")
        else:
            session = ClaudeSession(body["model"])
            sessions[session.id] = session
            stats["claude_sessions"] += 1
            await session.start(body, workdir, port)
        call_id = "call_" + uuid.uuid4().hex[:16]
        kind, event = await session.next_event()
        if kind == "reply" and not body.get("tools"):
            session.stop()
            sessions.pop(session.id, None)
            stats["claude_turns"] += 1
            text = event["result"].strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return completion(body["model"], text, [], session.spent(event))
        if kind == "reply":
            return await end_of_turn(session, body, event, call_id)
        name, arguments, future = event
        name = name.removeprefix(PREFIX)
        while name == "finish":
            future.set_result("The turn has ended.")
            try:
                kind, event = await asyncio.wait_for(session.next_event(), FINISH_SECONDS)
            except TimeoutError:
                session.stop()
                sessions.pop(session.id, None)
                raise HTTPException(502, "claude did not end its turn after finish") from None
            if kind == "reply":
                return await end_of_turn(session, body, event, call_id)
            name, arguments, future = event
            name = "finish"
        pending[call_id] = (session, future)
        return completion(body["model"], "", [(call_id, name, json.dumps(arguments))])

    @app.post("/bridge/{session_id}/call")
    async def bridge_call(session_id: str, request: Request):
        session = sessions.get(session_id)
        if not session:
            return {"content": "The task has ended."}
        body = await request.json()
        future = asyncio.get_running_loop().create_future()
        await session.events.put(("call", (body["name"], body["arguments"], future)))
        return {"content": await future}

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        body = await request.json()
        if body["model"].startswith("claude-"):
            return await claude_chat(body)
        if not openai_key:
            raise HTTPException(500, "Start the gateway with --openai-key-file for gpt models")
        return await openai_chat(client, openai_key, body)

    @app.get("/stats")
    async def read_stats():
        return {**stats, "claude_open": len(sessions), "claude_parked": len(parked)}

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--openai-key-file", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(name)s %(message)s")
    key = args.openai_key_file.read_text().strip() if args.openai_key_file else None
    uvicorn.run(create_app(key, args.port), host="127.0.0.1", port=args.port, log_level="warning")
