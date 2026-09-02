from typer.testing import CliRunner

runner = CliRunner()


def test_legacy_models_reexport_dedutive():
    from deductive_rca_bench.models import ScenarioCase
    from dedutive.models import ScenarioCase as NewScenarioCase

    assert ScenarioCase is NewScenarioCase


def test_legacy_data_loads_from_new_data_strategies_path():
    from deductive_rca_bench.data import load_cases, load_frameworks

    cases = load_cases()
    frameworks = load_frameworks()

    assert len(cases) == 30
    assert "kt" in frameworks["frameworks"]


def test_rca_bench_cli_still_works():
    from deductive_rca_bench.cli import app

    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "30 cases" in result.stdout


def test_rca_bench_score_cli_still_works():
    from deductive_rca_bench.cli import app

    result = runner.invoke(app, ["score", "--run", "tests/fixtures/sample_run.jsonl"])

    assert result.exit_code == 0
    assert "100" in result.stdout
