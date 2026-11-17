from examples.benchmarks.model_gateway import responses_request, transcript

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


def test_cli_prompt_is_the_bare_request_when_nothing_else_was_said():
    assert transcript(MESSAGES[:2]) == "Send Bob a message."
    assert "[tool result call_1]" in transcript(MESSAGES)
