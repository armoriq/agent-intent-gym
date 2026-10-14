from typer.testing import CliRunner

from agent_intent_bench.cli import app
from agent_intent_bench.store import Store

runner = CliRunner()


def test_scaffold_validate_run_export_and_gate(tmp_path):
    project = tmp_path / "my-evaluation"
    assert runner.invoke(app, ["new", str(project)]).exit_code == 0
    assert runner.invoke(app, ["validate", str(project / "scenario.yaml")]).exit_code == 0
    assert runner.invoke(app, ["new", str(project)]).exit_code != 0
    store = tmp_path / "artifacts"
    response = runner.invoke(
        app, ["run", "--suite", str(project / "scenario.yaml"), "--store", str(store)]
    )
    assert response.exit_code == 0, response.output
    run_id = Store(store).list()[0]["id"]
    assert runner.invoke(app, ["gate", run_id, "--store", str(store)]).exit_code == 0
    assert runner.invoke(app, ["verify", run_id, "--store", str(store)]).exit_code == 0
    csv = tmp_path / "episodes.csv"
    assert (
        runner.invoke(
            app, ["export", run_id, "--output", str(csv), "--format", "csv", "--store", str(store)]
        ).exit_code
        == 0
    )
    assert csv.exists()


def test_invalid_configuration_has_nonzero_exit(tmp_path):
    result = runner.invoke(
        app, ["run", "--suite", "smoke", "--agent", "http", "--store", str(tmp_path)]
    )
    assert result.exit_code == 2
    assert "endpoint" in result.output
