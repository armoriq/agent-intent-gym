"""Run a repository's tests on a throwaway copy inside a container.

The code under test may have been written by a model, so it never runs on the host. The
container has no network, a read-only file system, and sees nothing of the host except a
read-only mount of the copy. Only the Python standard library is needed inside it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path, PurePosixPath

IMAGE = os.environ.get("INTENTBENCH_SANDBOX_IMAGE", "python:3.12")
RESERVED = ".intentbench"
OUTPUT_LIMIT = 4000

# Imports every test_*.py under the target folder and calls its test_* functions.
RUNNER = """
import importlib.util, pathlib, sys, traceback

root = pathlib.Path.cwd()
sys.path.insert(0, str(root))
passed = failed = 0
for path in sorted((root / sys.argv[1]).rglob("test_*.py")):
    name = str(path.relative_to(root))
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except BaseException:
        failed += 1
        print("ERROR " + name)
        print("".join(traceback.format_exc().splitlines(True)[-4:]))
        continue
    for test, function in sorted(vars(module).items()):
        if test.startswith("test_") and callable(function):
            try:
                function()
                passed += 1
            except BaseException:
                failed += 1
                print("FAILED " + name + "::" + test)
                print("".join(traceback.format_exc().splitlines(True)[-4:]))
print(str(passed) + " passed, " + str(failed) + " failed" if passed or failed else "no tests ran")
sys.exit(0 if passed and not failed else 1)
"""


def relative_path(path: str) -> str | None:
    """The path as a clean repository-relative path, or None when it is not one."""
    if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
        return None
    parts = PurePosixPath(path).parts
    if not parts or ".." in parts or parts[0] == RESERVED:
        return None
    return str(PurePosixPath(*parts))


def run_tests(files: dict[str, str], target: str, timeout: float = 60) -> tuple[bool, str]:
    """Write `files` to a fresh folder and run the tests under `target`. Returns (green, output)."""
    root = Path(tempfile.mkdtemp(prefix="intentbench-repo-")).resolve()
    name = "intentbench-" + uuid.uuid4().hex[:12]
    try:
        for path, content in files.items():
            destination = (root / path).resolve()
            if not destination.is_relative_to(root):
                raise ValueError(f"File path leaves the repository copy: {path}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
        (root / RESERVED).mkdir(exist_ok=True)
        (root / RESERVED / "runner.py").write_text(RUNNER)
        command = [
            "docker", "run", "--rm", "--name", name,
            "--network", "none", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "512m",
            "--tmpfs", "/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "HOME=/tmp",
            "-v", f"{root}:/work:ro", "-w", "/work",
            IMAGE, "python", f"/work/{RESERVED}/runner.py", target,
        ]  # fmt: skip
        try:
            done = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            raise RuntimeError("Running repository tests needs Docker") from None
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            return False, "The test run timed out."
        if done.returncode not in (0, 1):
            raise RuntimeError("The test sandbox failed: " + done.stderr.strip()[-300:])
        return done.returncode == 0, (done.stdout + done.stderr)[-OUTPUT_LIMIT:].strip()
    finally:
        shutil.rmtree(root, ignore_errors=True)
