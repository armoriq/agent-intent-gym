"""Drive the gym from an existing agent/framework while keeping its own agent loop."""

from __future__ import annotations

from typing import Any

import httpx

from .models import Action, RunConfig


class GymClient:
    def __init__(self, endpoint: str = "http://127.0.0.1:8765", api_token: str | None = None):
        self.client = httpx.AsyncClient(
            base_url=endpoint,
            timeout=120,
            headers={"Authorization": f"Bearer {api_token}"} if api_token else {},
        )
        self.session_id: str | None = None
        self.session_token: str | None = None
        self.run_id: str | None = None

    async def reset(
        self, scenario_id: str, suite: str = "core", config: RunConfig | None = None
    ) -> dict[str, Any]:
        if self.session_id:
            await self.close_session()
        response = await self.client.post(
            "/v1/sessions",
            json={
                "suite": suite,
                "scenario_id": scenario_id,
                "config": (config or RunConfig()).model_dump(),
            },
        )
        response.raise_for_status()
        data = response.json()
        self.session_id, self.session_token, self.run_id = data["id"], data["token"], data["run_id"]
        return data["observation"]

    async def step(self, action: Action | dict[str, Any]) -> dict[str, Any]:
        if not self.session_id:
            raise ValueError("Call reset() before step()")
        validated = Action.model_validate(action)
        response = await self.client.post(
            f"/v1/sessions/{self.session_id}/step",
            json=validated.model_dump(),
            headers={"X-Session-Token": self.session_token},
        )
        response.raise_for_status()
        data = response.json()
        if data["done"]:
            self.session_id = self.session_token = None
        return data

    async def close_session(self) -> None:
        if self.session_id:
            response = await self.client.delete(
                f"/v1/sessions/{self.session_id}", headers={"X-Session-Token": self.session_token}
            )
            response.raise_for_status()
            self.session_id = self.session_token = None

    async def aclose(self) -> None:
        try:
            await self.close_session()
        finally:
            await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
