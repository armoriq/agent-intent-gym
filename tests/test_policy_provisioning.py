import json
from types import SimpleNamespace

import pytest
import yaml

from scripts.provision_armoriq import import_apikey, prepare, tool_catalog


def test_policy_preparation_preserves_conditions_and_limits_scope(tmp_path):
    documents = prepare(tmp_path, "00000000-0000-4000-8000-000000000001")
    assert len(documents) == 4
    for track, document in documents.items():
        assert document["target"] == {"agent": "intentbench-v2-" + track}
        assert document["spec"]["tools"]["default"] == "block"
        assert document["spec"]["capture"]["arguments"] is False
        registration = yaml.safe_load((tmp_path / track / "registration.yaml").read_text())
        assert registration["identity"]["api_key"] == "$ARMORIQ_API_KEY"
        assert registration["policy"] == {"allow": [], "deny": []}
    rules = documents["intent-gym"]["spec"]["tools"]["rules"]
    assert rules["payments__commit"][0]["when"] == {"args.quantity": {"lt": 0}}
    assert rules["payments__commit"][1]["when"] == {
        "args.beneficiary": {"eq": "ACME-APPROVED"},
        "args.quantity": {"lte": 100},
    }


@pytest.mark.parametrize("case", ["unauthorized", "invalid", "unbound", "inactive", "success"])
def test_curl_import_keeps_credentials_off_command_line_and_checks_activation(
    tmp_path, monkeypatch, case
):
    document = prepare(tmp_path, "00000000-0000-4000-8000-000000000001")["agentdojo"]
    key = "ak_test_stdin_only_fixture"

    def curl(command, *, input, **kwargs):
        assert command[0] == "curl"
        assert key not in repr(command)
        assert key in input
        assert command[command.index("--config") + 1] == "-"
        assert "https://api.armoriq.ai/policies/yaml/import-apikey" in command
        request = json.loads((tmp_path / "import-request.json").read_text())
        assert yaml.safe_load(request["yaml"]) == document and request["status"] == "active"
        diagnostics = (
            [{"severity": "error", "code": "parse"}]
            if case == "invalid"
            else [{"severity": "warning", "code": "unknown_tool_key"}]
            if case == "unbound"
            else []
        )
        response = {
            "policy": {
                "policyId": "benchmark-policy",
                "policyHash": "sha256:fixture",
                "status": "draft" if case == "inactive" else "active",
            },
            "diagnostics": diagnostics,
        }
        (tmp_path / "import-apikey-response.json").write_text(json.dumps(response))
        return SimpleNamespace(returncode=0, stdout="401" if case == "unauthorized" else "201")

    monkeypatch.setattr("scripts.provision_armoriq.subprocess.run", curl)
    if case == "success":
        result = import_apikey(document, tmp_path, key)
        assert result["status"] == "active" and result["policy_id"] == "benchmark-policy"
    else:
        with pytest.raises(RuntimeError) as error:
            import_apikey(document, tmp_path, key)
        assert key not in str(error.value)


def test_inventory_preserves_schema_variants_without_creating_permissions():
    schemas = [
        {"type": "object", "properties": {"amount": {"minimum": 1}}},
        {"type": "object", "properties": {"amount": {"minimum": 2}}},
    ]
    inventory = {
        "groups": [
            {
                "source": "core",
                "tools": [{"name": "payments__commit", "parameters": schema} for schema in schemas],
            }
        ]
    }
    catalog = tool_catalog("intent-gym", inventory)
    assert catalog == [
        {"name": "payments__commit", "description": "", "parameters": {"anyOf": schemas}}
    ]
    assert not tool_catalog("agentdojo", inventory)


def test_database_restore_checks_snapshot_before_touching_container(tmp_path, monkeypatch):
    from examples.benchmarks.stweb_snapshot import CONTAINER, restore

    path = tmp_path / "snapshot.sql"
    path.write_text("tampered contents")
    path.with_suffix(".json").write_text(
        json.dumps({"container": CONTAINER, "sha256": "original-digest"})
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Database must not be contacted for an invalid snapshot")

    monkeypatch.setattr("examples.benchmarks.stweb_snapshot.subprocess.run", forbidden)
    with pytest.raises(ValueError, match="integrity"):
        restore(task_id="47", seed=42, options={"database_snapshot": str(path)})
    with pytest.raises(ValueError, match="task 47"):
        restore(task_id="48", seed=42, options={"database_snapshot": str(path)})
