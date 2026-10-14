from __future__ import annotations

import json
import threading

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Footer, Header, RichLog, Static, TextArea

from .models import BenchmarkConfig
from .registry import benchmark_catalog
from .runner import run_benchmark
from .store import BenchmarkStore

DEFAULT_CONFIG = {
    "benchmark": "agentdojo",
    "task_ids": ["user_task_0"],
    "agent": {"kind": "http", "endpoint": "http://127.0.0.1:9001"},
    "options": {"suite": "workspace", "benchmark_version": "v1.2.2"},
    "mode": "unguarded",
    "seed": 42,
    "max_steps": 100,
}


class BenchmarkApp(App):
    TITLE = "ArmorIQ · Native benchmarks"
    BINDINGS = [("ctrl+r", "run", "Run"), ("ctrl+x", "stop", "Stop"), ("q", "quit", "Quit")]
    CSS = """
    #catalog { height: 9; }
    #config { height: 12; }
    #buttons { height: 3; }
    #status { height: 2; }
    #history { height: 7; }
    #result { height: 1fr; }
    Button { margin-right: 1; }
    """

    def __init__(self, config: BenchmarkConfig | None = None, store: BenchmarkStore | None = None):
        super().__init__()
        self.initial = config.model_dump(mode="json") if config else DEFAULT_CONFIG
        self.store = store or BenchmarkStore()
        self.stop = threading.Event()
        self.busy = False
        self.last_result = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="catalog")
        yield TextArea(json.dumps(self.initial, indent=2), id="config")
        with Horizontal(id="buttons"):
            yield Button("Run native benchmark", id="run", variant="success")
            yield Button("Stop at step boundary", id="stop", disabled=True)
        yield Static(
            "Native scores remain separate. Factor adaptations run in the ordinary gym.",
            id="status",
        )
        yield DataTable(id="history", cursor_type="row")
        yield RichLog(id="result", markup=False, wrap=True)
        yield Footer()

    def on_mount(self):
        table = self.query_one("#catalog", DataTable)
        table.add_columns("Source", "Role", "Dependencies / suite")
        for entry in benchmark_catalog():
            table.add_row(
                entry["name"],
                entry["role"],
                ", ".join(f"{k}: {v or 'missing'}" for k, v in entry["installed"].items())
                or entry["suite"],
            )
        self.query_one("#history", DataTable).add_columns(
            "Run", "Benchmark", "Complete", "Errors", "Truncated"
        )
        self.refresh_history()

    def refresh_history(self):
        table = self.query_one("#history", DataTable)
        table.clear()
        for row in self.store.list():
            table.add_row(
                row["id"],
                row["benchmark"],
                str(row["completed"]),
                str(row["error"]),
                str(row["truncated"]),
                key=row["id"],
            )

    @on(Button.Pressed)
    def button(self, event):
        if event.button.id == "run":
            self.action_run()
        else:
            self.action_stop()

    def action_run(self):
        if self.busy:
            return
        try:
            config = BenchmarkConfig.model_validate_json(self.query_one("#config", TextArea).text)
        except ValueError as error:
            self.notify(str(error), severity="error")
            return
        self.busy = True
        self.stop = threading.Event()
        self.query_one("#run", Button).disabled = True
        self.query_one("#stop", Button).disabled = False
        self.execute(config)

    @work(exclusive=True, exit_on_error=False)
    async def execute(self, config):
        try:

            def update(episode, count, total):
                self.call_from_thread(
                    self.query_one("#status", Static).update,
                    f"{count}/{total} · {episode.task_id} · {episode.status}",
                )

            self.last_result = await run_benchmark(config, self.store, update, self.stop)
            self.render_result(self.last_result)
            self.refresh_history()
        except Exception as error:
            from ..errors import safe_error

            self.notify(safe_error(error, config), severity="error")
        finally:
            self.busy = False
            self.query_one("#run", Button).disabled = False
            self.query_one("#stop", Button).disabled = True

    def action_stop(self):
        self.stop.set()
        self.query_one("#status", Static).update("Stopping at native step boundary…")

    def render_result(self, result):
        log = self.query_one("#result", RichLog)
        log.clear()
        log.write(json.dumps(result.model_dump(mode="json"), indent=2))

    @on(DataTable.RowSelected, "#history")
    def select_run(self, event):
        self.render_result(self.store.get(str(event.row_key.value)))
