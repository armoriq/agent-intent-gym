import asyncio
import json
import socket

import pytest

from scripts.run_runtime_intent_models import run

PLAN = json.dumps({"steps": [{"tool": "slack__read_channel", "args": {"channel": "general"}}]})


async def serve(reply):
    """A local endpoint that answers every request with `reply` (bytes), or just hangs up."""

    async def handle(reader, writer):
        if reply:
            await reader.read(65536)
            writer.write(reply)
            await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}/v1"


async def start(endpoint, tmp_path):
    return await run(["model-x"], 1, endpoint, tmp_path / "out.json", 1, reruns=0)


async def test_a_run_stops_when_nothing_listens_at_the_model_endpoint(tmp_path):
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    with pytest.raises(RuntimeError, match="not reachable"):
        await start(f"http://127.0.0.1:{port}/v1", tmp_path)


async def test_a_run_stops_when_the_control_case_cannot_complete(tmp_path):
    server, endpoint = await serve(None)
    async with server:
        with pytest.raises(RuntimeError, match="control case for model-x did not complete"):
            await start(endpoint, tmp_path)


async def test_a_run_that_measured_no_model_says_so(tmp_path):
    body = json.dumps({"choices": [{"message": {"content": PLAN}}]}).encode()
    head = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    server, endpoint = await serve(head.encode() + body)
    async with server:
        with pytest.raises(RuntimeError, match="No model was run"):
            await start(endpoint, tmp_path)
