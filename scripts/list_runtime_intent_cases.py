"""Print every model-facing run-time intent case as one Markdown page.

For each case: what the user asks, what the data or a failing call says, and the call an
agent makes if it follows that. Read it to review the cases; the suites themselves are built
by `examples/build_runtime_intent_model_suite.py` and `examples/build_runtime_intent_turns_suite.py`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples import build_coding_departures_suite as departures  # noqa: E402
from examples import build_coding_sessions_suite as coding  # noqa: E402
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


def steps(trace):
    """A scripted session as short lines, one per user turn."""
    lines, turn = [], []
    for action in trace:
        if action.get("kind") == "finish":
            lines.append("; ".join(turn) or "nothing")
            turn = []
        else:
            target = action["args"].get("path", "")
            turn.append((action["tool"].split("__")[1] + " " + target).strip())
    return [f"{number}. {line}" for number, line in enumerate(lines, start=1)]


def coding_page():
    suite = coding.build_suite()
    lines = [
        "# Coding sessions",
        "",
        f"Suite `{suite.id}` {suite.version}, {len(suite.scenarios)} sessions.",
        "",
    ]
    lines += ["## The repository", ""]
    for path, text in coding.FILES.items():
        lines += [f"`{path}`", "", "```", text.rstrip(), "```", ""]
    lines += ["## Turn 1 and the three levels", ""]
    for level, (request, files) in coding.LEVELS.items():
        lines += [f"Level `{level}`, turn 1:", "", quote(request), ""]
        for path, text in files.items():
            lines += [f"Added file `{path}`:", "", "```", text.rstrip(), "```", ""]
    lines += [
        "Allowed at every level after turn 1: write `querykit/query.py` and `CHANGELOG.md`; read anything except `.env`; list, search, run tests.",
        "",
        "Each session below exists once per level. Only turn 1 and the two rule files differ.",
        "",
    ]
    for kind, spec in coding.KINDS.items():
        lines += [f"## {kind}", ""]
        for path, text in spec.get("files", {}).items():
            lines += [f"Added file `{path}`:", "", "```", text.rstrip(), "```", ""]
        for number, turn in enumerate(spec["turns"], start=2):
            lines += [f"Turn {number}:", "", quote(turn["request"]), ""]
            granted = [f"write `{path}`" for path in turn.get("writes", [])]
            granted += [f"use `{tool}`" for tool in turn.get("tools", [])]
            granted += [
                f"`{tool}` only where {field} is {op} `{value}`"
                for tool, field, op, value in turn.get("rules", [])
            ]
            lines += ["Newly allowed: " + (", ".join(granted) or "nothing") + ".", ""]
        for name, title in (
            ("reference", "Stays in scope"),
            ("shortcut", "Shortcut, unauthorized"),
            ("eager", "Shortcut already in turn 1"),
        ):
            if name in coding.TRACES[kind]:
                lines += [f"{title}:", "", *steps(coding.TRACES[kind][name]), ""]
    return lines


def departures_page():
    suite = departures.build_suite()
    lines = [
        "# Coding departures",
        "",
        f"Suite `{suite.id}` {suite.version}, {len(suite.scenarios)} sessions, one user turn "
        "each, on the same repository as the coding sessions.",
        "",
        "The request, the same in every session:",
        "",
        quote(departures.REQUEST),
        "",
        "Allowed in every session: write and format `querykit/query.py` and `CHANGELOG.md`; "
        "read anything except `.env`; list, search, run tests.",
        "",
    ]
    for kind, spec in departures.KINDS.items():
        lines += [f"## {kind}", ""]
        if "refusal" in spec:
            lines += ["The first write to `querykit/query.py` fails with:", ""]
            lines += [quote(spec["refusal"]), "", "The same write works when it is retried.", ""]
        for path, text in spec.get("files", {}).items():
            lines += [f"`{path}` starts as:", "", "```", text.rstrip(), "```", ""]
        scripted = departures.traces(kind)
        lines += ["Stays in scope:", "", *steps(scripted["reference"]), ""]
        if "follow" in scripted:
            title = "Takes the way the push offers"
            title += ", unauthorized" if spec["variant"] == "attack" else ", allowed"
            lines += [title + ":", "", *steps(scripted["follow"]), ""]
    return lines


if __name__ == "__main__":
    pages = page("Single-turn cases", single) + page("Two-turn cases", turns) + coding_page()
    pages += departures_page()
    print("\n".join(pages))
