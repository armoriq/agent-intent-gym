"""Restore the dedicated local SuiteCRM database for native account task 47.

This resets database state only. It is not a general filesystem/website snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

CONTAINER = "intentbench-stweb-mariadb-1"
SNAPSHOT = Path(".benchmarks/snapshots/stweb-task47.sql")


def dump_database():
    return subprocess.run(
        [
            "docker",
            "exec",
            CONTAINER,
            "sh",
            "-c",
            'exec mariadb-dump -u root --single-transaction --skip-comments --order-by-primary "$MARIADB_DATABASE"',
        ],
        check=True,
        capture_output=True,
        timeout=120,
    ).stdout


def capture(path=SNAPSHOT):
    if path.exists():
        raise ValueError("Snapshot already exists; preserve it or choose a new path")
    data = dump_database()
    if not data:
        raise ValueError("Database dump was empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o600)
    metadata = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "container": CONTAINER,
        "scope": "SuiteCRM database only; native account task 47",
    }
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    return metadata


def restore(*, task_id, seed, options):
    if task_id != "47":
        raise ValueError("The local database snapshot is scoped to native task 47")
    path = Path(options.get("database_snapshot", str(SNAPSHOT)))
    metadata = json.loads(path.with_suffix(".json").read_text())
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if metadata.get("container") != CONTAINER or metadata.get("sha256") != digest:
        raise ValueError("Snapshot identity/integrity check failed before database restoration")
    subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "sh", "-c", 'exec mariadb -u root "$MARIADB_DATABASE"'],
        input=data,
        check=True,
        capture_output=True,
        timeout=120,
    )
    if hashlib.sha256(dump_database()).hexdigest() != digest:
        raise ValueError("Restored database did not match the captured logical snapshot")
    return {
        "snapshot_id": digest,
        "method": "SuiteCRM task47 MariaDB logical restore and digest verification; database only",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SNAPSHOT)
    args = parser.parse_args()
    metadata = capture(args.output)
    print(f"Captured task 47 database snapshot: {metadata['sha256']}")


if __name__ == "__main__":
    main()
