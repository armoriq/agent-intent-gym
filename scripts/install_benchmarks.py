"""Idempotent local runtimes for native benchmarks. Does not start cloud services or evaluate agents."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "agentdojo": (
        "https://github.com/ethz-spylab/agentdojo",
        "089ed468cf3ed0322acc66b0211f26d9d90dbf60",
    ),
    "stwebagentbench": (
        "https://github.com/segev-shlomov/ST-WebAgentBench",
        "67f56dd7df9eca1646c9e49407b087e950aa1e77",
    ),
    "doomarena": (
        "https://github.com/ServiceNow/DoomArena",
        "b80902f107b4d28194580352a59b3029f4a018b4",
    ),
    "interruptbench": (
        "https://github.com/HenryPengZou/InterruptBench",
        "17da111e4858b93c0cab1d88f85e1735fbd1d423",
    ),
    "agentlab": (
        "https://github.com/TanqiuJiang/AgentLAB",
        "36f58e60c36bbd6d5b8e61d50d7db7d9ea7258d7",
    ),
}


def install(name):
    base = ROOT / ".benchmarks"
    source, runtime = base / "sources" / name, base / "runtimes" / name
    (base / "logs").mkdir(parents=True, exist_ok=True)
    source.parent.mkdir(exist_ok=True)
    runtime.parent.mkdir(exist_ok=True)
    url, revision = SOURCES[name]
    if not source.exists():
        subprocess.run(["git", "clone", "--no-checkout", url, str(source)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(source),
                "-c",
                "filter.lfs.process=",
                "-c",
                "filter.lfs.smudge=",
                "-c",
                "filter.lfs.required=false",
                "checkout",
                revision,
            ],
            check=True,
        )
    actual = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != revision:
        raise ValueError(
            f"{name}: existing checkout differs from the tested revision; it was not overwritten"
        )
    if not runtime.exists():
        subprocess.run(["uv", "venv", str(runtime), "--python", "3.11"], check=True)
    python = str(runtime / "bin" / "python")
    required = {
        "agentdojo": ["agent-intent-bench", "agentdojo"],
        "stwebagentbench": ["agent-intent-bench", "browsergym-stwebagentbench", "nltk", "pandas"],
        "doomarena": ["agent-intent-bench", "doomarena-browsergym"],
        "interruptbench": ["webarena", "lxml", "anthropic", "dashscope"],
        "agentlab": ["openai", "anthropic", "json-repair", "pandas", "google-genai"],
    }[name]
    probe = subprocess.run(
        [
            python,
            "-c",
            "from importlib.metadata import version; "
            + repr(required)
            + "; "
            + "; ".join(f"version({package!r})" for package in required),
        ],
        capture_output=True,
    )
    ready = probe.returncode == 0
    if ready and name == "stwebagentbench":
        ready = (
            subprocess.check_output(
                [
                    python,
                    "-c",
                    "from importlib.metadata import version; print(version('playwright'))",
                ],
                text=True,
            ).strip()
            == "1.64.0"
        )
    packages = ["-e", str(ROOT)]
    if name == "agentdojo":
        packages += ["-e", str(source)]
    elif name == "stwebagentbench":
        packages += ["-e", str(source / "browsergym/stwebagentbench"), "openai", "nltk", "pandas"]
    elif name == "doomarena":
        packages += [
            "-e",
            str(source / "doomarena/core"),
            "-e",
            str(source / "doomarena/browsergym"),
        ]
    elif name == "interruptbench":
        # Its legacy pins conflict with the gym. This runtime runs the original harness directly.
        packages = [
            "-r",
            str(source / "Eval/requirements.txt"),
            "-e",
            str(source / "Eval"),
            "lxml",
            "anthropic==0.40.0",
            "dashscope==1.20.14",
        ]
    elif name == "agentlab":
        # CPU API-control profile only. Full upstream requirements conflict and include CUDA-only packages.
        packages = [
            "openai==1.109.1",
            "anthropic==0.71.0",
            "pandas==2.3.3",
            "tenacity==9.1.2",
            "json-repair",
            "tqdm==4.67.1",
            "loguru==0.7.3",
            "python-dotenv==1.2.1",
            "google-generativeai",
            "google-genai==1.59.0",
            "PyYAML==6.0.3",
            "fire==0.7.1",
        ]
    with (base / "logs" / f"setup-{name}.log").open("w") as log:
        if not ready:
            subprocess.run(
                ["uv", "pip", "install", "--python", python, *packages],
                check=True,
                stdout=log,
                stderr=log,
            )
        else:
            log.write("Installed package metadata found; existing runtime retained.\n")
        if name == "interruptbench":
            subprocess.run(
                [
                    python,
                    "-c",
                    "import nltk; assert nltk.download('punkt', download_dir="
                    + repr(str(runtime / "nltk_data"))
                    + ", quiet=True)",
                ],
                check=True,
                stdout=log,
                stderr=log,
            )
        if name == "stwebagentbench" and not ready:
            # Old bundled Chromium crashes on this macOS version, including the native Chat window.
            subprocess.run(
                ["uv", "pip", "install", "--python", python, "playwright==1.64.0"],
                check=True,
                stdout=log,
                stderr=log,
            )
        if name in {"stwebagentbench", "doomarena", "interruptbench"} and not ready:
            subprocess.run(
                [python, "-m", "playwright", "install", "chromium"],
                check=True,
                stdout=log,
                stderr=log,
            )
    freeze = subprocess.check_output(["uv", "pip", "freeze", "--python", python], text=True)
    (base / "logs" / f"{name}-freeze.txt").write_text(freeze)
    return {
        "revision": actual,
        "python": python,
        "profile": "CPU API control, no TextGrad/CUDA" if name == "agentlab" else "native runtime",
        "compatibility_override": "Playwright 1.64.0 replaces upstream <1.40 pin"
        if name == "stwebagentbench"
        else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmarks", nargs="*")
    args = parser.parse_args()
    if set(args.benchmarks) - SOURCES.keys():
        parser.error("Unknown benchmark; use " + ", ".join(SOURCES))
    report = {}
    for name in args.benchmarks or list(SOURCES):
        try:
            report[name] = {"status": "installed", **install(name)}
            print(f"{name}: installed")
        except (ValueError, subprocess.CalledProcessError) as error:
            report[name] = {"status": "error", "error": str(error)}
            print(f"{name}: inspect .benchmarks/logs/setup-{name}.log")
    (ROOT / ".benchmarks/install-manifest.json").write_text(json.dumps(report, indent=2))
    if any(item["status"] == "error" for item in report.values()):
        raise SystemExit(1)
