from __future__ import annotations

import asyncio
import hmac
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from importlib.resources import files
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import Field

from .adapters import close_adapter, create_guard
from .catalog import load_suite, validate_suite
from .errors import safe_error
from .metrics import aggregate
from .models import Action, Model, RunConfig, RunResult
from .runner import manifest_for, run_suite
from .session import Session, utc_now
from .store import Store


class RunRequest(Model):
    suite: str = "core"
    config: RunConfig = Field(default_factory=RunConfig)


class SessionRequest(RunRequest):
    scenario_id: str


def create_app(store: Store | None = None, default_config: RunConfig | None = None) -> FastAPI:
    from .settings import load_environment

    load_environment()
    store = store or Store()
    default_config = default_config or RunConfig()
    jobs: dict[str, dict[str, Any]] = {}
    sessions: dict[str, dict[str, Any]] = {}
    api_token = os.environ.get("INTENTBENCH_API_TOKEN")

    @asynccontextmanager
    async def lifespan(app):
        yield
        await shutdown_benchmarks()
        for job in jobs.values():
            job["stop"].set()
        tasks = [job["task"] for job in jobs.values() if not job["task"].done()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for item in list(sessions.values()):
            await finalize(item, "cancelled")

    app = FastAPI(title="ArmorIQ Agent Intent Gym", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        if request.url.path.startswith(("/api/", "/v1/")):
            origin = request.headers.get("origin")
            if origin and origin != f"{request.url.scheme}://{request.headers.get('host')}":
                return JSONResponse(
                    {"detail": "Cross-origin requests are not accepted"}, status_code=403
                )
            if request.method in {
                "POST",
                "PUT",
                "PATCH",
            } and "application/json" not in request.headers.get("content-type", ""):
                return JSONResponse({"detail": "Use application/json"}, status_code=415)
            if api_token:
                supplied = request.headers.get("authorization", "")
                if not hmac.compare_digest(supplied, f"Bearer {api_token}"):
                    return JSONResponse({"detail": "Set the workbench API token"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; object-src 'none'"
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return files("agent_intent_bench").joinpath("static/index.html").read_text()

    @app.get("/api/config")
    async def config():
        return default_config.model_dump()

    @app.get("/api/catalog")
    async def catalog(suite: str = "core"):
        try:
            data = load_suite(suite)
            validate_suite(data)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(400, str(error)) from error
        return {
            "id": data.id,
            "version": data.version,
            "description": data.description,
            "scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "domain": s.domain,
                    "family": s.family,
                    "variant": s.variant,
                    "request": s.request,
                    "tags": s.tags,
                    "rules": [r.model_dump() for r in s.intent.rules],
                }
                for s in data.scenarios
            ],
        }

    @app.post("/api/validate")
    async def validate(payload: RunRequest):
        try:
            data = load_suite(payload.suite)
            validate_suite(data)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(400, str(error)) from error
        return {"valid": True, "scenarios": len(data.scenarios)}

    @app.get("/api/runs")
    async def runs():
        return store.list()

    @app.get("/api/runs/{run_id}")
    async def run_result(run_id: str):
        try:
            return store.get(run_id)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(404, "Run not found or not yet complete") from error

    @app.post("/api/runs", status_code=202)
    async def start_run(payload: RunRequest):
        try:
            suite = load_suite(payload.suite)
            validate_suite(suite)
            from .runner import select_scenarios

            scenarios = select_scenarios(suite, payload.config)
            if payload.config.guard_policy and payload.config.guard.kind != "reference":
                raise ValueError("Policy overrides apply only to the reference guard")
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(400, str(error)) from error
        if sum(not job["task"].done() for job in jobs.values()) >= 4:
            raise HTTPException(429, "Four evaluations are already running")
        run_id = uuid.uuid4().hex[:12]
        job = {
            "status": "running",
            "completed": 0,
            "total": len(scenarios) * payload.config.repeats,
            "stop": asyncio.Event(),
            "error": None,
        }

        def progress(episode, completed, total):
            job.update(completed=completed, total=total, last_scenario=episode.scenario_id)

        async def execute():
            try:
                result = await run_suite(
                    suite, payload.config, store, progress, job["stop"], run_id
                )
                job["status"] = (
                    "cancelled"
                    if result.metrics["cancelled"]
                    else "error"
                    if result.metrics["errors"]
                    else "complete"
                )
            except Exception as error:
                job.update(status="error", error=safe_error(error, payload.config))

        job["task"] = asyncio.create_task(execute())
        jobs[run_id] = job
        return {"id": run_id, "total": job["total"]}

    @app.get("/api/jobs/{run_id}")
    async def job_status(run_id: str):
        if run_id not in jobs:
            raise HTTPException(404, "Active job not found")
        return {k: v for k, v in jobs[run_id].items() if k not in {"task", "stop"}}

    @app.post("/api/jobs/{run_id}/stop")
    async def stop_job(run_id: str):
        if run_id not in jobs:
            raise HTTPException(404, "Active job not found")
        jobs[run_id]["stop"].set()
        return {"status": "stopping"}

    async def finalize(item, status="completed", error=None):
        if item.get("closed"):
            return
        session = item["session"]
        episode = session.finish(status, 0, error)
        result = RunResult(
            id=item["run_id"],
            started_at=item["started_at"],
            suite_id=item["suite"].id,
            suite_version=item["suite"].version,
            manifest=item["manifest"],
            config=session.config,
            episodes=[episode],
            metrics=aggregate([episode], guarded=session.config.mode != "unguarded"),
        )
        store.save(result)
        item["closed"] = True
        if item["guard"]:
            await close_adapter(item["guard"])
        sessions.pop(session.id, None)

    def owned(session_id: str, request: Request):
        item = sessions.get(session_id)
        if not item or not hmac.compare_digest(
            request.headers.get("x-session-token", ""), item["token"]
        ):
            raise HTTPException(404, "Session not found")
        if session_elapsed(item) > item["session"].config.episode_timeout:
            raise HTTPException(
                408, "Session time budget expired; DELETE the session to finalize it"
            )
        return item

    def session_elapsed(item):
        import time

        return time.monotonic() - item["session"].started

    @app.post("/v1/sessions", status_code=201)
    async def create_session(payload: SessionRequest):
        if len(sessions) >= 32:
            raise HTTPException(429, "Close an active session before creating another")
        try:
            suite = load_suite(payload.suite)
            scenario = next((s for s in suite.scenarios if s.id == payload.scenario_id), None)
            if scenario is None:
                raise ValueError("Unknown scenario ID")
            config = payload.config.model_copy(deep=True)
            config.agent.kind = "external"
            config.repeats = 1
            validate_suite(suite)
            if config.guard_policy and config.guard.kind != "reference":
                raise ValueError("Policy overrides apply only to the reference guard")
            guard = (
                await asyncio.to_thread(create_guard, config.guard, config.guard_policy)
                if config.mode != "unguarded"
                else None
            )
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(400, str(error)) from error
        session_id, run_id = uuid.uuid4().hex, uuid.uuid4().hex[:12]
        session = Session(scenario, config, session_id, config.seed)
        subset = suite.model_copy(update={"scenarios": [scenario]})
        started, manifest = utc_now(), manifest_for(subset, config)
        store.begin(run_id, started, subset, config.model_dump(), manifest)
        token = secrets.token_urlsafe(32)
        item = {
            "session": session,
            "guard": guard,
            "token": token,
            "lock": asyncio.Lock(),
            "run_id": run_id,
            "suite": subset,
            "started_at": started,
            "manifest": manifest,
        }
        sessions[session_id] = item
        return {
            "id": session_id,
            "token": token,
            "run_id": run_id,
            "observation": session.observation(),
        }

    @app.get("/v1/sessions/{session_id}")
    async def observation(session_id: str, request: Request):
        item = owned(session_id, request)
        async with item["lock"]:
            return item["session"].observation()

    @app.post("/v1/sessions/{session_id}/step")
    async def step(session_id: str, action: Action, request: Request):
        item = owned(session_id, request)
        async with item["lock"]:
            session = item["session"]
            if session.step_index >= session.config.max_steps:
                await finalize(item, "truncated", "Step budget exceeded")
                raise HTTPException(409, "Step budget exceeded")
            try:
                async with asyncio.timeout(session.config.step_timeout):
                    result = await session.step(action, item["guard"])
            except Exception as error:
                await finalize(item, "error", safe_error(error, session.config))
                raise HTTPException(400, safe_error(error, session.config)) from error
            done = session.done
            response = {
                "result": result,
                "done": done,
                "run_id": item["run_id"],
                "observation": None if done else session.observation(),
            }
            if done:
                await finalize(item)
            return response

    @app.delete("/v1/sessions/{session_id}")
    async def delete_session(session_id: str, request: Request):
        # Expired sessions can still be closed and persisted.
        item = sessions.get(session_id)
        if not item or not hmac.compare_digest(
            request.headers.get("x-session-token", ""), item["token"]
        ):
            raise HTTPException(404, "Session not found")
        async with item["lock"]:
            await finalize(item, "cancelled")
        return {"status": "closed", "run_id": item["run_id"]}

    from .benchmarks.api import install_benchmark_routes

    shutdown_benchmarks = install_benchmark_routes(app, store.root)
    return app
