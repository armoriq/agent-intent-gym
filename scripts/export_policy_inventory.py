"""Export public tool schemas and SDK namespaces for authoring benchmark policies.

No model calls, backend requests, registration, or policy changes are performed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from agent_intent_bench.benchmarks.action_mapping import PARAMETERS
from agent_intent_bench.catalog import load_suite


def tool_entry(name, parameters=None, description="", default_mcp="intentbench"):
    mcp, separator, action = name.partition("__")
    if not separator:
        mcp, action = default_mcp, name
    return {
        "name": name,
        "agent_policy_key": name,
        # Legacy remote-MCP interpretation, not the v2 harness policy key.
        "mcp_name": mcp,
        "action": action,
        "cli_policy_ref": f"{mcp}.{action}",
        "description": description,
        "parameters": parameters,
    }


def export_inventory(runtime: Path, default_mcp="intentbench"):
    groups = []
    for name in ("core", "research-factors", "authorization-boundaries"):
        suite = load_suite(name)
        tools = {}
        for scenario in suite.scenarios:
            for tool in scenario.tools:
                entry = tool_entry(tool.name, tool.parameters, tool.description, default_mcp)
                # Retain schema variants rather than silently picking the first one.
                tools[json.dumps(entry, sort_keys=True)] = entry
        groups.append({"source": name, "tools": list(tools.values())})
    groups.append(
        {
            "source": "browser-action-mapper",
            "scope": "Supported mappings; native environments may expose a subset.",
            "tools": [
                {
                    **tool_entry("browser__" + name, default_mcp=default_mcp),
                    "argument_names": list(parameters),
                }
                for name, parameters in PARAMETERS.items()
            ],
        }
    )
    missing = []
    python = runtime / "bin/python"
    if python.is_file():
        # Load public schemas only, without creating tasks, graders, agents, or SDK clients.
        program = """
import json
from agentdojo.task_suite.load_suites import get_suite
print(json.dumps({name: [
    {"name": t.name, "description": t.description,
     "parameters": t.parameters.model_json_schema()}
    for t in get_suite("v1.2.2", name).tools
] for name in ("workspace", "travel", "banking", "slack")}))
"""
        completed = subprocess.run(
            [str(python.absolute()), "-c", program],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        for name, tools in json.loads(completed.stdout).items():
            entries = [
                tool_entry(t["name"], t["parameters"], t["description"], default_mcp) for t in tools
            ]
            entries.append(
                tool_entry(
                    "agent__respond",
                    {
                        "type": "object",
                        "properties": {"output": {"type": "string"}},
                        "required": ["output"],
                        "additionalProperties": False,
                    },
                    "Final native answer, checked when guard_responses is true.",
                    default_mcp,
                )
            )
            groups.append({"source": "agentdojo/" + name, "version": "v1.2.2", "tools": entries})
    else:
        missing.append("AgentDojo runtime unavailable; install it to export native tool schemas")
    return {
        "schema_version": "policy-inventory-1.0",
        "purpose": "Policy authoring inventory. Tool presence does not grant authorization.",
        "tool_name_mode": "agent",
        "namespace_note": "Harness v2 rules use agent_policy_key (the full name). MCP/CLI fields describe the legacy remote-server mapping only.",
        "default_mcp_name": default_mcp,
        "policy_coverage": "unverified",
        "groups": groups,
        "missing": missing,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".intentbench/policy-inventory.json"))
    parser.add_argument(
        "--agentdojo-runtime", type=Path, default=Path(".benchmarks/runtimes/agentdojo")
    )
    parser.add_argument("--default-mcp", default="intentbench")
    args = parser.parse_args()
    inventory = export_inventory(args.agentdojo_runtime, args.default_mcp)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, allow_nan=False) + "\n")
    print(f"Saved {args.output} ({len(inventory['groups'])} tool groups)")
    for issue in inventory["missing"]:
        print(issue)


if __name__ == "__main__":
    main()
