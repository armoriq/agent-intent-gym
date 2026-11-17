"""Local chat-completions gateway so one agent adapter can drive every evaluated model.

`gpt-*` models go to the OpenAI Responses API with native function tools, because the
chat-completions endpoint refuses function tools on reasoning models.

`claude-*` models go to the `claude` CLI in print mode with its built-in tools, settings,
other MCP servers and slash commands switched off. One CLI process serves one episode. The
episode's tools reach the model as real tools through `mcp_tool_bridge.py`; each call is
handed to the benchmark and its result is returned to the same process, so tool calls and
history are native. Tool names carry the prefix `mcp__gym__` on that route.

Neither route accepts a temperature or a seed, so runs are repeated instead of seeded.
The OpenAI key is read from a file given on the command line and never logged.

    uv run --no-sync python -m examples.benchmarks.model_gateway --openai-key-file PATH
"""

import argparse
import asyncio
import json
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request

EFFORT = "medium"
IDLE_SECONDS = 180
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
        "reasoning": {"effort": EFFORT},
        "store": False,
    }
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


async def openai_chat(client, key, body):
    response = await client.post(
        "https://api.openai.com/v1/responses",
        json=responses_request(body),
        headers={"Authorization": "Bearer " + key},
    )
    if response.status_code != 200:
        error = response.json().get("error", {})
        raise HTTPException(502, f"OpenAI {response.status_code}: {error.get('message', '')}")
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


def tokens(usage):
    return {
        "prompt_tokens": sum(
            usage.get(k, 0)
            for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        ),
        "completion_tokens": usage.get("output_tokens", 0),
    }


class ClaudeSession:
    """One `claude -p` process whose tool calls are answered by the benchmark."""

    def __init__(self, model):
        self.id = uuid.uuid4().hex[:12]
        self.model = model
        self.calls = asyncio.Queue()
        self.process = None
        self.finished = None
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
            "--output-format",
            "json",
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
        )
        self.finished = asyncio.create_task(
            self.process.communicate(transcript(body["messages"]).encode())
        )

    async def next_event(self):
        """Wait for the model's next tool call, or for its final reply."""
        waiting = asyncio.create_task(self.calls.get())
        await asyncio.wait({waiting, self.finished}, return_when=asyncio.FIRST_COMPLETED)
        self.touched = time.monotonic()
        if waiting.done():
            return "call", waiting.result()
        waiting.cancel()
        stdout, _ = self.finished.result()
        try:
            data = json.loads(stdout)
        except ValueError:
            raise HTTPException(502, f"claude exited {self.process.returncode}") from None
        if data.get("is_error") or not isinstance(data.get("result"), str):
            raise HTTPException(502, f"claude returned no reply: {data.get('subtype')}")
        if self.model not in data.get("modelUsage", {}):
            raise HTTPException(502, f"claude answered with {sorted(data.get('modelUsage', {}))}")
        return "reply", data

    def stop(self):
        if self.process and self.process.returncode is None:
            self.process.kill()


def create_app(openai_key=None, port=8791):
    app = FastAPI()
    workdir = tempfile.mkdtemp(prefix="model-gateway-")
    client = httpx.AsyncClient(timeout=600)
    sessions, pending = {}, {}
    stats = {"claude_sessions": 0, "claude_completed": 0, "claude_stopped_idle": 0}

    def sweep():
        for session in list(sessions.values()):
            if time.monotonic() - session.touched > IDLE_SECONDS:
                session.stop()
                sessions.pop(session.id, None)
                stats["claude_stopped_idle"] += 1
                for call_id, (owner, future) in list(pending.items()):
                    if owner is session:
                        pending.pop(call_id)
                        future.cancel()

    async def claude_chat(body):
        sweep()
        trailing = []
        for message in reversed(body["messages"]):
            if message["role"] == "assistant":
                break
            trailing.insert(0, message)
        answered = [m for m in trailing if m["role"] == "tool" and m["tool_call_id"] in pending]
        if answered:
            session, future = pending.pop(answered[0]["tool_call_id"])
            future.set_result("\n\n".join(m.get("content") or "" for m in trailing))
        else:
            session = ClaudeSession(body["model"])
            sessions[session.id] = session
            stats["claude_sessions"] += 1
            await session.start(body, workdir, port)
        kind, event = await session.next_event()
        if kind == "reply":
            sessions.pop(session.id, None)
            stats["claude_completed"] += 1
            text = event["result"].strip()
            if not body.get("tools"):
                text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return completion(body["model"], text, [], tokens(event.get("usage", {})))
        name, arguments, future = event
        name = name.removeprefix(PREFIX)
        call_id = "call_" + uuid.uuid4().hex[:16]
        if name == "finish":
            future.set_result("The task has ended.")
            sessions.pop(session.id, None)
            stats["claude_completed"] += 1
        else:
            pending[call_id] = (session, future)
        return completion(body["model"], "", [(call_id, name, json.dumps(arguments))])

    @app.post("/bridge/{session_id}/call")
    async def bridge_call(session_id: str, request: Request):
        session = sessions.get(session_id)
        if not session:
            return {"content": "The task has ended."}
        body = await request.json()
        future = asyncio.get_running_loop().create_future()
        await session.calls.put((body["name"], body["arguments"], future))
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
        return {**stats, "claude_open": len(sessions)}

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--openai-key-file", type=Path)
    args = parser.parse_args()
    key = args.openai_key_file.read_text().strip() if args.openai_key_file else None
    uvicorn.run(create_app(key, args.port), host="127.0.0.1", port=args.port, log_level="warning")
