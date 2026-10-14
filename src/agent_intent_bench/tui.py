from __future__ import annotations

import asyncio
import json

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    RichLog,
    Select,
    SelectionList,
    Static,
    TabbedContent,
    TabPane,
)

from .catalog import load_suite
from .cli import percentage
from .models import RunConfig
from .runner import run_suite
from .store import Store


class IntentBenchApp(App):
    TITLE = "ArmorIQ · Agent Intent Gym"
    SUB_TITLE = "Intent → plan → action → effect"
    BINDINGS = [
        ("ctrl+r", "run_suite", "Run"),
        ("ctrl+x", "cancel_run", "Stop"),
        ("ctrl+h", "history", "History"),
        ("q", "quit", "Quit"),
    ]
    CSS = """
    Screen { background: #101821; }
    Header { background: #172735; color: #cfe8ef; }
    Footer { background: #172735; }
    TabbedContent { height: 1fr; }
    TabPane { height: 1fr; }
    #intro { height: 3; padding: 1 2; color: #54ddbb; background: #14232d; }
    #configure { overflow-y: auto; }
    #suite-row { height: 3; padding: 0 1; }
    #suite-path { width: 1fr; }
    .controls { height: 5; padding: 0 1; }
    .field { width: 1fr; padding: 0 1; }
    .field Label { height: 1; color: #8eabb8; }
    Select, Input { border: tall #29414e; background: #15222e; }
    #work-area { height: 1fr; min-height: 8; }
    #scenarios { width: 56%; border: round #29414e; margin: 0 1; }
    #scenario-info { width: 44%; padding: 1 2; border: round #29414e; margin-right: 1; overflow-y: auto; }
    #actions { height: 3; padding: 0 1; }
    #status { width: 1fr; padding: 1 2; color: #8eabb8; }
    Button { margin-right: 1; }
    Button.-primary { background: #167c6a; }
    #progress { height: 1; margin: 0 2; }
    #run-summary { height: auto; min-height: 5; padding: 1 2; color: #d7e7ed; background: #14232d; }
    #runs, #episodes { height: 1fr; margin: 1; }
    #trace-top { height: 40%; min-height: 8; }
    #events { width: 55%; }
    #event-detail { width: 45%; border: round #29414e; }
    #trace-log { height: 1fr; margin: 1; border: round #29414e; }
    .hint { height: 2; padding: 0 2; color: #8eabb8; }
    """

    def __init__(self, suite: str, config: RunConfig, store: Store):
        super().__init__()
        self.suite_path = suite
        self.settings = config
        self.store = store
        self.active_stop: asyncio.Event | None = None
        self.last_result = None
        self.current_episode = None
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "AGENT INTENT GYM  /  Evaluate agent behavior, guard decisions, and authorized outcomes",
            id="intro",
        )
        with TabbedContent(initial="configure", id="tabs"):
            with TabPane("Configure & run", id="configure"):
                with Horizontal(id="suite-row"):
                    yield Input(
                        self.suite_path, placeholder="Built-in suite or YAML path", id="suite-path"
                    )
                    yield Button("Load suite", id="load")
                with Horizontal(classes="controls"):
                    with Vertical(classes="field"):
                        yield Label("Agent")
                        yield Select(
                            [
                                (name, name)
                                for name in dict.fromkeys(
                                    [
                                        self.settings.agent.kind,
                                        "careful",
                                        "gullible",
                                        "stubborn",
                                        "chaotic",
                                        "http",
                                        "openai",
                                        "python",
                                    ]
                                )
                            ],
                            value=self.settings.agent.kind,
                            allow_blank=False,
                            id="agent",
                        )
                    with Vertical(classes="field"):
                        yield Label("Guard")
                        yield Select(
                            [
                                (name, name)
                                for name in [
                                    "reference",
                                    "armoriq",
                                    "plan",
                                    "allow",
                                    "deny",
                                    "http",
                                    "python",
                                ]
                            ],
                            value=self.settings.guard.kind,
                            allow_blank=False,
                            id="guard",
                        )
                    with Vertical(classes="field"):
                        yield Label("Execution mode")
                        yield Select(
                            [(name, name) for name in ["enforce", "monitor", "unguarded"]],
                            value=self.settings.mode,
                            allow_blank=False,
                            id="mode",
                        )
                with Horizontal(classes="controls"):
                    for name, value in [
                        ("repeats", self.settings.repeats),
                        ("seed", self.settings.seed),
                        ("max_steps", self.settings.max_steps),
                        ("concurrency", self.settings.concurrency),
                    ]:
                        with Vertical(classes="field"):
                            yield Label(name.replace("_", " ").title())
                            yield Input(str(value), type="integer", id=name)
                with Horizontal(id="work-area"):
                    yield SelectionList[str](id="scenarios")
                    yield Static(
                        "Load a suite to inspect its intent factors.",
                        id="scenario-info",
                        markup=False,
                    )
                with Horizontal(id="actions"):
                    yield Button("Run evaluation", variant="primary", id="run")
                    yield Button("Stop", variant="error", id="stop", disabled=True)
                    yield Button("Select all", id="select-all")
                    yield Button("Clear", id="clear")
                    yield Static("Ready · offline fixtures need no credentials", id="status")
                yield ProgressBar(total=100, show_eta=False, id="progress")
            with TabPane("Results & history", id="history"):
                yield Static(
                    "Run an evaluation or select a saved run below.", id="run-summary", markup=False
                )
                yield DataTable(id="runs", cursor_type="row")
                yield Label(
                    "Select a run to inspect its episodes; press Enter on an episode for its trace.",
                    classes="hint",
                )
                yield DataTable(id="episodes", cursor_type="row")
            with TabPane("Trace inspector", id="trace"):
                with Horizontal(id="trace-top"):
                    yield DataTable(id="events", cursor_type="row")
                    yield RichLog(id="event-detail", wrap=True, markup=False)
                yield RichLog(id="trace-log", wrap=True, markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#runs", DataTable).add_columns(
            "Run", "Suite", "Agent / guard", "Mode", "Status", "CuP", "Effects"
        )
        self.query_one("#episodes", DataTable).add_columns(
            "Scenario", "Status", "CuP", "Proposals", "Effects", "Plans"
        )
        self.query_one("#events", DataTable).add_columns(
            "#", "Event / tool", "Oracle", "Guard", "Effect"
        )
        self.load_scenarios()
        self.refresh_history()

    def load_scenarios(self) -> None:
        try:
            self.suite_path = self.query_one("#suite-path", Input).value
            suite = load_suite(self.suite_path)
            selection = self.query_one("#scenarios", SelectionList)
            selection.clear_options()
            selection.add_options(
                [
                    (
                        s.name,
                        s.id,
                        not self.settings.scenario_ids or s.id in self.settings.scenario_ids,
                    )
                    for s in suite.scenarios
                ]
            )
            self.query_one("#scenario-info", Static).update(
                f"{suite.id.upper()} · v{suite.version}\n\n{suite.description}\n\n{len(suite.scenarios)} scenarios\n\nSelect scenarios on the left.\n\nAgents: scripted fixtures, native Python, HTTP, or model endpoints.\n\nGuards: reference policy, native ArmorIQ SDK, HTTP, or Python.\n\nEndpoint and SDK settings come from the --config YAML file."
            )
            self.query_one("#status", Static).update(
                f"{len(selection.selected)} scenarios selected"
            )
        except Exception as error:
            self.notify(str(error), severity="error")

    @on(SelectionList.SelectedChanged)
    def selection_changed(self) -> None:
        if not self.busy:
            self.query_one("#status", Static).update(
                f"{len(self.query_one('#scenarios', SelectionList).selected)} scenarios selected"
            )

    @on(SelectionList.SelectionHighlighted)
    def scenario_highlighted(self, event: SelectionList.SelectionHighlighted) -> None:
        try:
            scenario = next(
                s for s in load_suite(self.suite_path).scenarios if s.id == event.selection.value
            )
            self.query_one("#scenario-info", Static).update(
                f"{scenario.name}\n\n{scenario.request}\n\nFACTOR: {scenario.family}\nVARIANT: {scenario.variant}\n\n"
                + "\n".join(f"• {r.description}" for r in scenario.intent.rules)
            )
        except (ValueError, StopIteration):
            pass

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "load": self.load_scenarios,
            "run": self.action_run_suite,
            "stop": self.action_cancel_run,
            "select-all": lambda: self.query_one("#scenarios", SelectionList).select_all(),
            "clear": lambda: self.query_one("#scenarios", SelectionList).deselect_all(),
        }
        if event.button.id in actions:
            actions[event.button.id]()

    def action_run_suite(self) -> None:
        if self.busy:
            return
        try:
            selected = list(self.query_one("#scenarios", SelectionList).selected)
            if not selected:
                raise ValueError("Select at least one scenario")
            data = self.settings.model_dump()
            for key in ("repeats", "seed", "max_steps", "concurrency"):
                data[key] = int(self.query_one(f"#{key}", Input).value)
            data["agent"]["kind"] = self.query_one("#agent", Select).value
            data["guard"]["kind"] = self.query_one("#guard", Select).value
            data["mode"] = self.query_one("#mode", Select).value
            data["scenario_ids"] = selected
            settings = RunConfig.model_validate(data)
            suite = load_suite(self.query_one("#suite-path", Input).value)
        except Exception as error:
            self.notify(str(error), severity="error")
            return
        self.busy = True
        self.active_stop = asyncio.Event()
        self.query_one("#run", Button).disabled = True
        self.query_one("#stop", Button).disabled = False
        self.query_one("#progress", ProgressBar).update(
            total=len(selected) * settings.repeats, progress=0
        )
        self.execute(suite, settings)

    @work(exclusive=True, exit_on_error=False)
    async def execute(self, suite, settings) -> None:
        try:

            def progress(episode, completed, total):
                self.query_one("#progress", ProgressBar).update(progress=completed)
                self.query_one("#status", Static).update(
                    f"{completed}/{total} · {episode.scenario_id} · {episode.status}"
                )

            self.last_result = await run_suite(
                suite, settings, self.store, progress, self.active_stop
            )
            self.display_result(self.last_result)
            self.refresh_history()
            self.query_one("#tabs", TabbedContent).active = "history"
            self.query_one("#runs", DataTable).focus()
        except Exception as error:
            self.notify(str(error), severity="error", timeout=10)
        finally:
            self.busy = False
            self.query_one("#run", Button).disabled = False
            self.query_one("#stop", Button).disabled = True

    def action_cancel_run(self) -> None:
        if self.active_stop:
            self.active_stop.set()
            self.query_one("#status", Static).update("Stopping · preserving completed traces…")

    def action_history(self) -> None:
        self.refresh_history()
        self.query_one("#tabs", TabbedContent).active = "history"
        self.query_one("#runs", DataTable).focus()

    def refresh_history(self) -> None:
        table = self.query_one("#runs", DataTable)
        table.clear()
        for row in self.store.list():
            table.add_row(
                row["id"],
                row["suite"],
                f"{row['agent']} / {row['guard']}",
                row["mode"],
                row["status"],
                percentage(row["cup"]),
                percentage(row["effects"]),
                key=row["id"],
            )

    def display_result(self, result) -> None:
        self.last_result = result
        m = result.metrics
        self.query_one("#run-summary", Static).update(
            f"{result.id} · {result.config.agent.kind} → {result.config.guard.kind} · {result.config.mode}\n"
            f"Completion under policy {percentage(m['completion_under_policy'])}    Unauthorized effects {percentage(m['unauthorized_effect_rate'])}\n"
            f"Agent proposal drift {percentage(m['proposal_drift_rate'])}    Guard detection {percentage(m['guard_detection_rate'])}    Overblocking {percentage(m['guard_overblocking_rate'])}\n"
            f"Coverage {percentage(m['coverage'])}    Errors {m['errors']}    Truncated {m['truncated']}    Artifacts {self.store.path(result.id)}"
        )
        table = self.query_one("#episodes", DataTable)
        table.clear()
        for episode in result.episodes:
            table.add_row(
                episode.scenario_id,
                episode.status,
                "yes" if episode.completion_under_policy else "no",
                str(episode.proposal_violations),
                str(episode.effect_violations),
                str(episode.plan_violations),
                key=episode.id,
            )

    @on(DataTable.RowSelected)
    def row_selected(self, event: DataTable.RowSelected) -> None:
        key = str(event.row_key.value)
        if event.data_table.id == "runs":
            try:
                self.display_result(self.store.get(key))
            except FileNotFoundError:
                self.notify("This run is still in progress")
        elif event.data_table.id == "episodes" and self.last_result:
            self.current_episode = next(e for e in self.last_result.episodes if e.id == key)
            table = self.query_one("#events", DataTable)
            table.clear()
            log = self.query_one("#trace-log", RichLog)
            log.clear()
            for item in self.current_episode.events:
                tool = item.action.tool if item.action and item.action.tool else item.kind
                table.add_row(
                    str(item.seq),
                    tool,
                    "deviation"
                    if item.verdict and not item.verdict.allowed
                    else "allowed"
                    if item.verdict
                    else "—",
                    item.decision.action if item.decision else "—",
                    "committed" if item.committed else "—",
                    key=str(item.seq),
                )
                if item.verdict and not item.verdict.allowed:
                    for violation in item.verdict.violations:
                        log.write(
                            f"Step {item.seq} · {violation.severity.upper()} · {violation.rule_id}\n{violation.description}\n{json.dumps(violation.evidence, indent=2)}\n"
                        )
            if self.current_episode.error:
                log.write(self.current_episode.error)
            if not any(e.verdict and not e.verdict.allowed for e in self.current_episode.events):
                log.write("No independently scored contract deviations in this episode.")
            self.query_one("#event-detail", RichLog).clear()
            self.query_one("#tabs", TabbedContent).active = "trace"
            self.query_one("#events", DataTable).focus()
        elif event.data_table.id == "events" and self.current_episode:
            detail = self.query_one("#event-detail", RichLog)
            detail.clear()
            detail.write(
                json.dumps(self.current_episode.events[int(key)].model_dump(mode="json"), indent=2)
            )
