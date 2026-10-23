"""Install the same ArmorIQ SDK into the gym and three native agent runtimes."""

import argparse
import json
import subprocess
import tomllib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sdk-path", type=Path, help="Existing customer SDK checkout; otherwise use PyPI"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    locked_sdk = next(
        p["version"]
        for p in tomllib.loads((root / "uv.lock").read_text())["package"]
        if p["name"] == "armoriq-sdk"
    )
    package = (
        ["-e", str(args.sdk_path.resolve())] if args.sdk_path else ["armoriq-sdk==" + locked_sdk]
    )
    runtimes = [root / ".venv"] + [
        root / ".benchmarks/runtimes" / name
        for name in ("agentdojo", "stwebagentbench", "doomarena")
    ]
    missing = [str(r) for r in runtimes if not (r / "bin/python").exists()]
    if missing:
        raise SystemExit("Install gym and native runtimes first: " + ", ".join(missing))
    inventory = {}
    for runtime in runtimes:
        python = str(runtime / "bin/python")
        # Both distributions import as armoriq_sdk; leaving an editable customer
        # SDK alongside the public wheel makes provenance and imports ambiguous.
        subprocess.run(
            ["uv", "pip", "uninstall", "--python", python, "armoriq-sdk", "armoriq-sdk-dev"],
            check=True,
        )
        subprocess.run(
            ["uv", "pip", "install", "--python", python, *package, "python-dotenv>=1,<2"],
            check=True,
        )
        probe = subprocess.check_output(
            [
                python,
                "-c",
                "import importlib.metadata as m, json; from armoriq_sdk import ArmorIQClient, SessionOptions; "
                "print(json.dumps({d.metadata['Name']: d.version for d in m.distributions() "
                "if d.metadata['Name'] in ('armoriq-sdk', 'armoriq-sdk-dev')}))",
            ],
            text=True,
        )
        inventory[str(runtime.relative_to(root))] = json.loads(probe)
    destination = root / ".benchmarks/armoriq-install.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(inventory, indent=2))
    print(
        "Installed SDK in gym + AgentDojo/ST-WebAgentBench/DoomArena runtimes. Use uv run --no-sync."
    )


if __name__ == "__main__":
    main()
