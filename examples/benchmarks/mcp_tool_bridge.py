"""Stdio MCP server that forwards every tool call to the local model gateway.

Started by the `claude` CLI, one process per episode. It advertises the tools listed in a
JSON file and executes nothing itself: each call is posted to the gateway, which hands it to
the benchmark and returns the benchmark's result.

    python mcp_tool_bridge.py TOOLS_JSON CALL_URL
"""

import json
import sys
import urllib.request


def tool_result(reply):
    """The MCP result for the gateway's reply; a blocked or failed call is an error."""
    return {
        "content": [{"type": "text", "text": reply["content"]}],
        "isError": bool(reply.get("isError")),
    }


def main(tools_path, call_url):
    tools = json.load(open(tools_path))
    for line in sys.stdin:
        if not line.strip():
            continue
        message = json.loads(line)
        method, request_id = message.get("method"), message.get("id")
        if request_id is None:
            continue
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "gym", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("parameters") or {"type": "object"},
                    }
                    for tool in tools
                ]
            }
        elif method == "tools/call":
            body = json.dumps(
                {
                    "name": message["params"]["name"],
                    "arguments": message["params"].get("arguments") or {},
                }
            ).encode()
            request = urllib.request.Request(call_url, body, {"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=1800) as response:
                result = tool_result(json.load(response))
        else:
            result = {}
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
