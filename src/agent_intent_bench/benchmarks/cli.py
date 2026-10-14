from __future__ import annotations

import asyncio
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .models import BenchmarkConfig
from .registry import SOURCES, benchmark_catalog
from .runner import run_benchmark
from .store import BenchmarkStore

app = typer.Typer(no_args_is_help=True, help="Native benchmarks and attributed factor designs")
console = Console()


def load_benchmark_config(path: Path) -> BenchmarkConfig:
    return BenchmarkConfig.model_validate(yaml.safe_load(path.read_text()))


@app.command("list")
def list_benchmarks():
    table = Table("Benchmark", "Integration", "Dependencies / suite", "Results")
    for entry in benchmark_catalog():
        dependencies = ", ".join(
            f"{k} {v or '(not installed)'}" for k, v in entry["installed"].items()
        )
        if entry["local_runtime"]:
            dependencies = "Isolated runtime installed: " + entry["local_runtime"]
        table.add_row(
            entry["name"],
            entry["role"],
            dependencies or entry["suite"],
            "Run-specific; none bundled",
        )
    console.print(table)


@app.command()
def inspect(benchmark: str):
    if benchmark not in SOURCES:
        console.print("Unknown benchmark")
        raise typer.Exit(2)
    console.print_json(data=next(e for e in benchmark_catalog() if e["id"] == benchmark))


@app.command()
def run(config: Path, store: Path = Path(".intentbench")):
    """Run a native adapter configuration, keeping the original grader outputs."""
    try:
        settings = load_benchmark_config(config)
        result = asyncio.run(
            run_benchmark(
                settings,
                BenchmarkStore(store),
                lambda e, n, total: console.print(f"{n}/{total} · {e.task_id} · {e.status}"),
            )
        )
        console.print(f"Saved {result.id} · {BenchmarkStore(store).path(result.id)}")
        for episode in result.episodes:
            console.print_json(
                data={
                    "task_id": episode.task_id,
                    "status": episode.status,
                    "native_scores": episode.native_scores,
                    "derived_scores": episode.derived_scores,
                    "error": episode.error,
                }
            )
        if result.summary["error"] or result.summary["cancelled"]:
            raise typer.Exit(2)
        if result.summary["truncated"]:
            raise typer.Exit(1)
    except (ValueError, FileNotFoundError, ImportError) as error:
        console.print(f"[red]{type(error).__name__}: {error}[/]")
        raise typer.Exit(2) from error


@app.command()
def history(store: Path = Path(".intentbench")):
    console.print_json(data=BenchmarkStore(store).list())


@app.command()
def tui(config: Path | None = None, store: Path = Path(".intentbench")):
    """Configure native adapters, run evaluations, and inspect their original scores."""
    from .tui import BenchmarkApp

    BenchmarkApp(load_benchmark_config(config) if config else None, BenchmarkStore(store)).run()


@app.command()
def show(run_id: str, store: Path = Path(".intentbench")):
    console.print_json(data=BenchmarkStore(store).get(run_id).model_dump(mode="json"))


@app.command()
def verify(run_id: str, store: Path = Path(".intentbench")):
    if not BenchmarkStore(store).verify(run_id):
        console.print("[red]Artifacts differ from saved hashes[/]")
        raise typer.Exit(1)
    console.print("[green]Native result, manifest, and config hashes verified[/]")
