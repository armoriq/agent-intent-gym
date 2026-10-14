import time

import pytest
from fastapi.testclient import TestClient

from agent_intent_bench.api import create_app
from agent_intent_bench.store import Store


def test_browser_job_runs_and_artifacts_available(tmp_path):
    with TestClient(create_app(Store(tmp_path))) as client:
        assert client.get("/").status_code == 200
        assert len(client.get("/api/catalog?suite=smoke").json()["scenarios"]) == 9
        response = client.post(
            "/api/runs", json={"suite": "smoke", "config": {"agent": {"kind": "gullible"}}}
        )
        assert response.status_code == 202
        run_id = response.json()["id"]
        for _ in range(100):
            job = client.get(f"/api/jobs/{run_id}").json()
            if job["status"] != "running":
                break
            time.sleep(0.02)
        assert job["status"] == "complete"
        result = client.get(f"/api/runs/{run_id}").json()
        assert result["metrics"]["guard_detection_rate"] == 1
        assert result["metrics"]["unauthorized_effect_rate"] == 0
        assert client.get("/api/runs").json()[0]["id"] == run_id


def test_agent_session_boundary_hides_oracle_and_requires_ownership(tmp_path):
    with TestClient(create_app(Store(tmp_path))) as client:
        created = client.post(
            "/v1/sessions", json={"suite": "smoke", "scenario_id": "email.injection.clean"}
        )
        assert created.status_code == 201
        data = created.json()
        assert "oracle_intent" not in str(data["observation"])
        assert "verdict" not in data["observation"]
        path = f"/v1/sessions/{data['id']}"
        assert client.get(path).status_code == 404
        headers = {"X-Session-Token": data["token"]}
        observation = client.get(path, headers=headers).json()
        assert observation["episode_id"] == data["id"]
        finished = client.post(path + "/step", json={"kind": "finish"}, headers=headers)
        assert finished.json()["done"]
        assert client.get(path, headers=headers).status_code == 404
        result = client.get(f"/api/runs/{data['run_id']}").json()
        assert result["config"]["agent"]["kind"] == "external"
        assert result["metrics"]["completion_under_policy"] == 0


def test_cross_origin_mutations_and_non_json_posts_rejected(tmp_path):
    with TestClient(create_app(Store(tmp_path))) as client:
        assert (
            client.post(
                "/api/runs", json={}, headers={"Origin": "https://attacker.test"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/runs", content="{}", headers={"Content-Type": "text/plain"}
            ).status_code
            == 415
        )


def test_api_token_and_invalid_run_path(tmp_path, monkeypatch):
    monkeypatch.setenv("INTENTBENCH_API_TOKEN", "test-service-token")
    with TestClient(create_app(Store(tmp_path))) as client:
        assert client.get("/api/config").status_code == 401
        assert (
            client.get(
                "/api/config", headers={"Authorization": "Bearer test-service-token"}
            ).status_code
            == 200
        )
    store = Store(tmp_path)
    with pytest.raises(ValueError):
        store.path("../escape")


def test_custom_yaml_and_invalid_selection_errors(tmp_path):
    with TestClient(create_app(Store(tmp_path))) as client:
        assert client.post("/api/runs", json={"suite": "unknown"}).status_code == 400
        assert (
            client.post(
                "/api/runs", json={"suite": "smoke", "config": {"scenario_ids": ["unknown"]}}
            ).status_code
            == 400
        )
