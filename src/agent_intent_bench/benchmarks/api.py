from __future__ import annotations

import asyncio
import threading
import uuid
from pathlib import Path

import yaml
from fastapi import HTTPException

from ..errors import safe_error
from .models import BenchmarkConfig
from .registry import benchmark_catalog
from .runner import run_benchmark
from .store import BenchmarkStore


def install_benchmark_routes(app, root):
    store = BenchmarkStore(root)
    jobs = {}

    @app.get("/api/benchmarks")
    async def catalog():
        return benchmark_catalog()

    @app.get("/api/benchmarks/default-config")
    async def default_config():
        path = Path(".benchmarks/configs/agentdojo-workspace-qwen.yaml")
        if path.exists():
            return BenchmarkConfig.model_validate(yaml.safe_load(path.read_text())).model_dump(
                mode="json"
            )
        return {
            "benchmark": "agentdojo",
            "task_ids": ["user_task_0"],
            "agent": {"kind": "http", "endpoint": "http://127.0.0.1:9001"},
            "options": {"suite": "workspace", "benchmark_version": "v1.2.2"},
        }

    @app.get("/api/benchmarks/runs")
    async def history():
        return store.list()

    @app.get("/api/benchmarks/runs/{run_id}")
    async def result(run_id: str):
        try:
            return store.get(run_id)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(404, "Native run not found or still running") from error

    @app.post("/api/benchmarks/validate")
    async def validate(config: BenchmarkConfig):
        return {
            "valid": True,
            "benchmark": config.benchmark,
            "tasks": len(config.task_ids),
            "note": "Configuration validated; native dependencies and services checked at runtime",
        }

    @app.post("/api/benchmarks/runs", status_code=202)
    async def start(config: BenchmarkConfig):
        if sum(not job["task"].done() for job in jobs.values()) >= 2:
            raise HTTPException(429, "Two native benchmark jobs are already running")
        run_id = uuid.uuid4().hex[:12]
        job = {
            "status": "running",
            "completed": 0,
            "total": len(config.task_ids) * config.repeats,
            "stop": threading.Event(),
            "error": None,
        }
        loop = asyncio.get_running_loop()

        def update(episode, count, total):
            loop.call_soon_threadsafe(
                lambda: job.update(completed=count, total=total, last_task=episode.task_id)
            )

        async def execute():
            try:
                result = await run_benchmark(config, store, update, job["stop"], run_id)
                job["status"] = (
                    "error"
                    if result.summary["error"]
                    else "cancelled"
                    if result.summary["cancelled"]
                    else "complete"
                )
            except Exception as error:
                job.update(status="error", error=safe_error(error, config))

        job["task"] = asyncio.create_task(execute())
        jobs[run_id] = job
        return {"id": run_id}

    @app.get("/api/benchmarks/jobs/{run_id}")
    async def status(run_id: str):
        if run_id not in jobs:
            raise HTTPException(404, "Job not found")
        return {key: value for key, value in jobs[run_id].items() if key not in {"task", "stop"}}

    @app.post("/api/benchmarks/jobs/{run_id}/stop")
    async def stop(run_id: str):
        if run_id not in jobs:
            raise HTTPException(404, "Job not found")
        jobs[run_id]["stop"].set()
        return {"status": "stopping_at_native_step_boundary"}

    async def shutdown():
        for job in jobs.values():
            job["stop"].set()
        if jobs:
            await asyncio.gather(*(j["task"] for j in jobs.values()), return_exceptions=True)

    return shutdown
