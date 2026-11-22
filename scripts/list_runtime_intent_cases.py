"""Print every model-facing run-time intent case as one Markdown page.

For each case: what the user asks, what the data or a failing call says, and the call an
agent makes if it follows that. Read it to review the cases; the suites themselves are built
by `examples/build_runtime_intent_model_suite.py` and `examples/build_runtime_intent_turns_suite.py`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples import build_runtime_intent_model_suite as single  # noqa: E402
from examples import build_runtime_intent_turns_suite as turns  # noqa: E402


def quote(text):
    return "\n".join("> " + line for line in text.strip().splitlines())


def shown(call):
    return f"`{call['tool']}` {json.dumps(call['args'])}" if call else "none"


def added_text(scenario, clean):
    """What this case's reads return beyond the clean case, plus any failing call."""

    def reads(s):
        texts = {}
        for tool in s.tools:
            content = (
                (tool.response or {}).get("content") if isinstance(tool.response, dict) else None
            )
            if isinstance(content, str):
                texts[tool.name] = content
        for tool, entries in s.initial_state.get("sources", {}).items():
            for key, text in entries.items() if isinstance(entries, dict) else [("", entries)]:
                texts[f"{tool} {key}".strip()] = text
        return texts

    before, parts = reads(clean), []
    for name, text in reads(scenario).items():
        extra = text[len(before.get(name, "")) :] if text.startswith(before.get(name, "")) else text
        if extra.strip():
            parts.append(f"Added to what `{name}` returns:\n\n{quote(extra)}")
    for fault in scenario.disturbances:
        turn = f" in turn {fault.turn + 1}" if scenario.turns else ""
        parts.append(
            f"The first requested `{fault.payload['tool']}` call{turn} fails with:\n\n"
            + quote(fault.payload["message"])
        )
    return "\n\n".join(parts) or "Nothing added."


def page(title, module):
    suite = module.build_suite()
    lines = [
        f"# {title}",
        "",
        f"Suite `{suite.id}` {suite.version}, {len(suite.scenarios)} cases.",
        "",
    ]
    by_family = {}
    for scenario in suite.scenarios:
        by_family.setdefault(scenario.family, []).append(scenario)
    for family, scenarios in by_family.items():
        clean = next(s for s in scenarios if s.id.endswith(".clean"))
        lines += [f"## {family}", "", "User request:", "", quote(clean.request), ""]
        for scenario in scenarios:
            kind = scenario.id.rsplit(".", 1)[1]
            lines += [f"### {scenario.id}", ""]
            for number, turn in enumerate(scenario.turns, start=2):
                lines += [f"Turn {number} request:", "", quote(turn.request), ""]
            lines += [added_text(scenario, clean), ""]
            lines += [
                "Unauthorized call if the agent follows it: "
                + shown(module.extra_call(family, kind)),
                "",
            ]
    return lines


if __name__ == "__main__":
    print("\n".join(page("Single-turn cases", single) + page("Two-turn cases", turns)))
