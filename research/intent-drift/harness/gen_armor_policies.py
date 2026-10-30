#!/usr/bin/env python3
"""Emit real armor.policy.v1 PolicyProfiles, one per benchmark domain.

Grounded in the ArmorClaude plugin IR (armorClaude/scripts/lib/policy-ir.mjs and
POLICY_GUIDE.md): a PolicyProfile with defaults.decision = deny, conflict
resolution deny_overrides, and statements using effect permit|forbid on
action.type = tool with file.path conditions. Each benchmark task's intent
contract (one permitted target file, four forbidden rabbit holes) maps directly:

  - permit  Edit/Write/MultiEdit where file.path within the permitted module
  - forbid  Edit/Write/MultiEdit where file.path is a cross-file rabbit hole
  - default deny everything else (fail-closed)

The one same-file rabbit hole (the old_<fn> alias, in the permitted module) is
NOT separable by a file.path condition; it is recorded under
notes.same_file_residue so the precision accounting downstream is honest about
what a path-level policy cannot catch.

Reads:  armor-intent/intents.yaml
Writes: armor-intent/policies/<task>.policy.json  (+ index.json)
Usage:  python3 harness/gen_armor_policies.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "armor-intent", "intents.yaml")
OUTDIR = os.path.join(ROOT, "armor-intent", "policies")

WRITE_TOOLS = ["Edit", "Write", "MultiEdit"]


def parse_intents():
    txt = open(SRC).read()
    recs = []
    for b in re.split(r"\n  - task: ", txt)[1:]:
        slug = b.split("\n", 1)[0].strip()
        allow = re.search(r"allow_edit: (\S+)", b).group(1)
        intent = re.search(r'intent: "(.*)"', b).group(1)
        denies = re.findall(r"- (repo/\S+)", b)
        recs.append(dict(slug=slug, allow=allow, intent=intent, denies=denies))
    return recs


def policy_for(rec):
    allow_file = rec["allow"].split(":")[0]
    cross = [d for d in rec["denies"] if d.split(":")[0] != allow_file]
    same = [d for d in rec["denies"] if d.split(":")[0] == allow_file]
    statements = [
        {
            "id": "permit-fix-target",
            "effect": "permit",
            "principal": {"type": "agent", "id": "*"},
            "action": {"type": "tool", "in": WRITE_TOOLS},
            "resource": {"type": "file", "scope": "current"},
            "conditions": [
                {"field": "file.path", "op": "eq", "value": allow_file}
            ],
        }
    ]
    for i, d in enumerate(sorted(set(f.split(":")[0] for f in cross))):
        statements.append({
            "id": "forbid-rabbit-hole-%d" % (i + 1),
            "effect": "forbid",
            "principal": {"type": "agent", "id": "*"},
            "action": {"type": "tool", "in": WRITE_TOOLS},
            "resource": {"type": "file", "scope": "current"},
            "conditions": [
                {"field": "file.path", "op": "eq", "value": d}
            ],
        })
    return {
        "schemaVersion": "armor.policy.v1",
        "kind": "PolicyProfile",
        "metadata": {
            "name": "intentbench-%s" % rec["slug"],
            "description": "Intent contract for %s. %s" % (rec["slug"], rec["intent"]),
        },
        "defaults": {"decision": "deny", "conflictResolution": "deny_overrides"},
        "statements": statements,
        "notes": {
            "permitted_target_symbol": rec["allow"],
            "cross_file_forbidden": cross,
            "same_file_residue": same,
        },
    }


def build():
    os.makedirs(OUTDIR, exist_ok=True)
    recs = parse_intents()
    index = []
    for rec in recs:
        pol = policy_for(rec)
        path = os.path.join(OUTDIR, "%s.policy.json" % rec["slug"])
        with open(path, "w") as f:
            json.dump(pol, f, indent=2)
            f.write("\n")
        index.append({
            "task": rec["slug"],
            "policy": os.path.basename(path),
            "permit": rec["allow"],
            "forbid_cross_file": len(pol["notes"]["cross_file_forbidden"]),
            "same_file_residue": len(pol["notes"]["same_file_residue"]),
        })
    with open(os.path.join(OUTDIR, "index.json"), "w") as f:
        json.dump({"schemaVersion": "armor.policy.v1",
                   "count": len(index), "policies": index}, f, indent=2)
        f.write("\n")
    cross = sum(i["forbid_cross_file"] for i in index)
    same = sum(i["same_file_residue"] for i in index)
    print("wrote %d policies to %s" % (len(index), OUTDIR))
    print("cross-file forbidden (path-deterministic): %d" % cross)
    print("same-file residue (needs fn/content gate):  %d" % same)


if __name__ == "__main__":
    build()
