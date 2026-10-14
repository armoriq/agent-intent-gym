from textual.widgets import DataTable, TabbedContent

from agent_intent_bench.models import RunConfig
from agent_intent_bench.store import Store
from agent_intent_bench.tui import IntentBenchApp


async def test_tui_run_history_and_trace(tmp_path):
    app = IntentBenchApp("smoke", RunConfig(), Store(tmp_path))
    async with app.run_test(size=(130, 44)) as pilot:
        await pilot.pause()
        assert app.query_one("#run").region.bottom <= app.size.height - 1
        await pilot.click("#run")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.last_result is not None
        assert app.last_result.metrics["errors"] == 0
        assert app.query_one("#tabs", TabbedContent).active == "history"
        episodes = app.query_one("#episodes", DataTable)
        assert episodes.row_count == 9
        episodes.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.query_one("#tabs", TabbedContent).active == "trace"
        assert app.query_one("#events", DataTable).row_count > 0


async def test_tui_empty_selection_does_not_start_run(tmp_path):
    from textual.widgets import SelectionList

    app = IntentBenchApp("smoke", RunConfig(), Store(tmp_path))
    async with app.run_test(size=(130, 44)) as pilot:
        app.query_one("#scenarios", SelectionList).deselect_all()
        await pilot.click("#run")
        await pilot.pause()
        assert app.last_result is None
        assert not app.busy
