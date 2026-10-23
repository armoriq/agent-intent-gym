"""Prepare, register, compile, and activate dedicated benchmark v2 policies.

Preparation is the default. --register uses the installed Python CLI with local
state files. --apply uses curl and the API-key-compatible YAML import endpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import jsonschema
import yaml

from agent_intent_bench.settings import load_environment

ROOT = Path(__file__).resolve().parents[1]
TRACKS = ("intent-gym", "agentdojo", "stwebagentbench", "doomarena")


def tool_catalog(track, inventory):
    sources = (
        {"core", "research-factors"}
        if track == "intent-gym"
        else {"agentdojo/workspace"}
        if track == "agentdojo"
        else {"browser-action-mapper"}
    )
    tools = {}
    for group in inventory["groups"]:
        if group["source"] not in sources:
            continue
        for entry in group["tools"]:
            name = entry["name"]
            tool = tools.setdefault(
                name, {"name": name, "description": entry.get("description", ""), "schemas": {}}
            )
            schema = entry.get("parameters")
            if schema is not None:
                tool["schemas"][json.dumps(schema, sort_keys=True)] = schema
    result = []
    for _, tool in sorted(tools.items()):
        schemas = list(tool.pop("schemas").values())
        tool["parameters"] = (
            schemas[0] if len(schemas) == 1 else {"anyOf": schemas} if schemas else None
        )
        result.append(tool)
    return result


def import_apikey(document, folder, key):
    request = folder / "import-request.json"
    request.write_text(
        json.dumps({"yaml": yaml.safe_dump(document, sort_keys=False), "status": "active"})
    )
    response_path = folder / "import-apikey-response.json"
    # Credentials enter curl on stdin, never the shell, process arguments, or logs.
    config = (
        "header = "
        + json.dumps("x-api-key: " + key)
        + '\nheader = "Content-Type: application/json"\n'
    )
    completed = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--max-time",
            "45",
            "--request",
            "POST",
            "https://api.armoriq.ai/policies/yaml/import-apikey",
            "--config",
            "-",
            "--data-binary",
            "@" + str(request),
            "--output",
            str(response_path),
            "--write-out",
            "%{http_code}",
        ],
        input=config,
        text=True,
        capture_output=True,
    )
    if completed.returncode or completed.stdout not in {"200", "201"}:
        raise RuntimeError(
            f"curl policy import failed: exit {completed.returncode}, HTTP {completed.stdout}"
        )
    response_path.chmod(0o600)
    data = json.loads(response_path.read_text())
    diagnostics = data.get("diagnostics", [])
    if any(
        d.get("severity") == "error" or d.get("code") == "unknown_tool_key" for d in diagnostics
    ):
        raise RuntimeError(
            "Policy import has errors or unbound tool keys; inspect import-apikey-response.json"
        )
    record = data.get("policy", {})
    if record.get("status") != "active" or not record.get("policyId"):
        raise RuntimeError("API-key import did not confirm an active policy identifier")
    return {
        "policy_id": record["policyId"],
        "policy_hash": record.get("policyHash"),
        "status": "active",
        "diagnostics": diagnostics,
    }


def write_runtime_profile(root, agents, policies):
    source = ROOT / "examples/armoriq-inside"
    profile = yaml.safe_load((source / "experiment.yaml").read_text())
    folder = root / "run-configs"
    folder.mkdir(exist_ok=True)
    for track in profile["tracks"]:
        config = yaml.safe_load((source / track["config"]).read_text())
        identity = config.get("benchmark", "intent-gym")
        catalog = root / identity / "tools.json"
        config["guard"]["options"].update(
            agent_id=agents[policies[identity]["target"]["agent"]],
            tool_catalog=str(catalog),
            tool_catalog_sha256=hashlib.sha256(catalog.read_bytes()).hexdigest(),
        )
        destination = folder / Path(track["config"]).name
        destination.write_text(yaml.safe_dump(config, sort_keys=False))
        track["config"] = "run-configs/" + destination.name
    (root / "experiment.yaml").write_text(yaml.safe_dump(profile, sort_keys=False))


def prepare(root: Path, org_id: str, deployment: str | None = None):
    source = ROOT / "examples/armoriq-inside/policies"
    schema = json.loads((ROOT / "docs/schemas/armor-policy-v2-benchmark.schema.json").read_text())
    policies = {}
    for track in TRACKS:
        document = yaml.safe_load((source / f"{track}.yaml").read_text())
        document["metadata"]["orgId"] = org_id
        if deployment:
            document["metadata"]["name"] += "-" + deployment
            document["target"]["agent"] += "-" + deployment
            document["metadata"]["labels"]["deployment"] = deployment
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(
            document
        )
        folder = root / track
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "policy.yaml").write_text(yaml.safe_dump(document, sort_keys=False))
        registration = {
            "version": "v1",
            "identity": {
                "api_key": "$ARMORIQ_API_KEY",
                "user_id": "intentbench-evaluation-user",
                "agent_id": document["target"]["agent"],
            },
            "environment": "sandbox",
            "mcp_servers": [],
            # Registration only: no lossy conversion of conditional v2 rules.
            "policy": {"allow": [], "deny": []},
        }
        (folder / "registration.yaml").write_text(yaml.safe_dump(registration, sort_keys=False))
        policies[track] = document
    return policies


def api(client, method, path, body=None):
    response = client.request(method, path, json=body)
    if response.status_code >= 400:
        # Avoid echoing backend responses that may contain account data or tokens.
        raise RuntimeError(f"{method} {path}: HTTP {response.status_code}")
    return response.json()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--deployment", help="Unique campaign suffix; use a new value when policies change"
    )
    parser.add_argument("--output", type=Path, default=Path(".benchmarks/policy-setup"))
    args = parser.parse_args()
    if args.deployment and not all(c.isalnum() or c == "-" for c in args.deployment):
        raise SystemExit("Deployment suffix accepts only letters, digits, and hyphens")
    load_environment()
    from armoriq_sdk._build_env import resolve

    base = os.environ.get("ARMORIQ_BACKEND_ENDPOINT") or resolve("backend")
    key = os.environ.get("ARMORIQ_API_KEY")
    if not key:
        raise SystemExit("Set ARMORIQ_API_KEY in .env")
    root = args.output.resolve()
    if args.deployment:
        root = root / args.deployment
    root.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=base, headers={"X-API-Key": key}, timeout=30) as client:
        bootstrap = api(client, "POST", "/iap/sdk/bootstrap", {})
    org_id = bootstrap["org"]["orgId"]
    policies = prepare(root, org_id, args.deployment)
    report_path = root / "provisioning.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    if report.get("org_id") != org_id:
        report = {
            "schema": "armor.io/v2",
            "sdk": "0.8.17",
            "org_id": org_id,
            "agents": {},
            "policies": {},
        }
    report.pop("error", None)
    try:
        if args.register:
            # CLI and SDK endpoint override names differ.
            os.environ.setdefault("ARMORIQ_BACKEND_URL", base)
            from armoriq_sdk import cli

            cli.STATE_DIR = root / "cli-state"
            cli.STATE_FILE = cli.STATE_DIR / "state.json"
            cli.LOG_FILE = cli.STATE_DIR / "cli.log"
            for track in policies:
                result = cli.main(["register", "--config", str(root / track / "registration.yaml")])
                if result:
                    raise RuntimeError(f"Python CLI registration failed for {track}")
                report["agents"][track] = "registered"
                report_path.write_text(json.dumps(report, indent=2))
        if args.apply:
            # Refresh after registrations to get canonical platform IDs.
            with httpx.Client(base_url=base, headers={"X-API-Key": key}, timeout=30) as client:
                bootstrap = api(client, "POST", "/iap/sdk/bootstrap", {})
                agents = {a["name"]: a["agentId"] for a in bootstrap.get("agents", [])}
                from armoriq_sdk.tool_registry import ToolDeclaration, ToolRegistry

                inventory_path = root / "tool-inventory.json"
                subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/export_policy_inventory.py"),
                        "--output",
                        str(inventory_path),
                    ],
                    check=True,
                )
                inventory = json.loads(inventory_path.read_text())
                for track, document in policies.items():
                    agent_id = agents.get(document["target"]["agent"])
                    if not agent_id:
                        raise RuntimeError(f"Register the dedicated {track} agent first")
                    tools = tool_catalog(track, inventory)
                    (root / track / "tools.json").write_text(json.dumps(tools, indent=2))
                    registry = ToolRegistry()
                    registry.register(
                        agent_id,
                        [
                            ToolDeclaration(
                                name=t["name"],
                                description=t["description"],
                                input_schema=t["parameters"],
                                schema_source="framework" if t["parameters"] else "none",
                            )
                            for t in tools
                        ],
                    )
                    response = api(client, "POST", "/iap/sdk/tools", registry.push_body(agent_id))
                    (root / track / "tool-registration.json").write_text(
                        json.dumps(response, indent=2)
                    )
                    source_digest = hashlib.sha256(
                        yaml.safe_dump(document, sort_keys=False).encode()
                    ).hexdigest()
                    previous = report["policies"].get(track)
                    if previous:
                        if previous.get("source_sha256") != source_digest:
                            raise RuntimeError(
                                "A deployed policy changed; choose a new --deployment suffix"
                            )
                        bundle = api(client, "GET", "/policy/bundles/current?agent=" + agent_id)
                        active = next(
                            (
                                a.get("policy")
                                for a in bundle.get("agents", [])
                                if a.get("agentId") == agent_id and not a.get("inactive")
                            ),
                            None,
                        )
                        if not active or active.get("policyHash") != previous.get("policy_hash"):
                            raise RuntimeError(
                                "Previously deployed policy no longer matches the platform"
                            )
                    else:
                        report["policies"][track] = {
                            **import_apikey(document, root / track, key),
                            "source_sha256": source_digest,
                        }
                    report_path.write_text(json.dumps(report, indent=2))
                write_runtime_profile(root, agents, policies)
        print(f"Prepared {len(policies)} policies in {root}")
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
