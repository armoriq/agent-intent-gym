"""Check staged/tracked publication files; print paths/reasons, never secret values."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

PRIVATE_PARTS = {
    ".env",
    ".venv",
    ".benchmarks",
    ".intentbench",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "dist",
    "build",
    "logs",
    "log_files",
    ".DS_Store",
}
PATTERNS = {
    "private key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "GitHub token": rb"(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})",
    "model API key": rb"sk-[A-Za-z0-9_-]{20,}",
    "Google API key": rb"AIza[A-Za-z0-9_-]{35}",
    "AWS access key": rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
    "ArmorIQ production key": rb"ak_(?:live|prod)_[A-Za-z0-9_-]{20,}",
}
SECRET_NAME = re.compile(
    r"(?:API_KEY|ACCESS_TOKEN|AUTH_TOKEN|PASSWORD|SECRET|GH_TOKEN|GITHUB_TOKEN)$"
)


def local_secrets(root: Path) -> list[bytes]:
    values = dict(os.environ)
    if (root / ".env").is_file():
        from dotenv import dotenv_values

        # Preserve both sources, even when a shell override shadows the local file.
        file_values = dotenv_values(root / ".env", interpolate=False)
    else:
        file_values = {}
    return list(
        {
            str(value).encode()
            for source in (values, file_values)
            for name, value in source.items()
            if SECRET_NAME.search(name) and value and len(str(value)) >= 8
        }
    )


def findings(path: str, content: bytes, secrets: list[bytes]) -> list[str]:
    parts = PurePosixPath(path).parts
    name = PurePosixPath(path).name
    issues = []
    if set(parts) & PRIVATE_PARTS or (name.startswith(".env") and name != ".env.example"):
        issues.append("private/runtime artifact")
    if name.endswith((".log", ".pyc")):
        issues.append("generated log/cache")
    if len(content) > 2 * 1024 * 1024:
        issues.append("file exceeds 2 MiB publication limit")
    for label, pattern in PATTERNS.items():
        if re.search(pattern, content):
            issues.append(label)
    if any(secret in content for secret in secrets):
        issues.append("local credential value")
    if name == ".env.example":
        for line in content.decode().splitlines():
            key, _, value = line.partition("=")
            if SECRET_NAME.search(key.strip()) and value.strip():
                issues.append("example credential must be blank")
    return issues


def main() -> int:
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    paths = (
        subprocess.check_output(["git", "ls-files", "--cached", "-z"], cwd=root)
        .decode()
        .split("\0")
    )
    paths = sorted(set(filter(None, paths)))
    if not paths:
        print("No staged/tracked files. Stage the intended publication files first.")
        return 1
    secrets = local_secrets(root)
    problems = []
    for path in paths:
        content = subprocess.check_output(["git", "show", ":" + path], cwd=root)
        issues = findings(path, content, secrets)
        if issues:
            problems.append((path, issues))
    for path, issues in problems:
        print(path + ": " + ", ".join(issues))
    if problems:
        return 1
    print(
        f"Publication check passed for {len(paths)} staged/tracked files; no detected credentials or private artifacts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
