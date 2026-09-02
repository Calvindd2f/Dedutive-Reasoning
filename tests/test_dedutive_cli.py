from pathlib import Path

from typer.testing import CliRunner

from dedutive.providers.base import GenerationResult

runner = CliRunner()

_STUB_RESPONSE_JSON = (
    '{"problem_frame":"stub","known_facts":[],"key_unknowns":[],'
    '"hypotheses":[{"name":"stub","confidence":0.5,"why_it_fits":[]}],'
    '"next_best_tests":[],"decision":{"chosen_path":"stub","why":"stub","risks":[]},'
    '"execution_plan":["stub"],"verification_steps":[],'
    '"nits_brief":{"nature":"n","intention":"i","time":"t","special_instructions":"s"},'
    '"post_incident_learning":{"loop_type":"single_loop","lesson":"stub"}}'
)


class _RecordingStubProvider:
    """Stub provider that records every messages payload it was called with.

    Mirrors tests/test_orchestrator_runtime.py's _StubProvider, but also
    captures the rendered system-message content so callers can assert on
    which reasoning/decision/learning strategy was actually applied.
    """

    calls: list[list[dict[str, str]]] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    def generate(self, messages, *, model, temperature, response_format=None):
        _RecordingStubProvider.calls.append(messages)
        return GenerationResult(text=_STUB_RESPONSE_JSON, metadata={"provider": "stub"})


def test_dedutive_scenario_validate_smoke():
    from dedutive.cli import app

    result = runner.invoke(app, ["scenario", "validate"])

    assert result.exit_code == 0
    assert "30 cases" in result.stdout


def test_dedutive_frameworks_list_smoke():
    from dedutive.cli import app

    result = runner.invoke(app, ["frameworks", "list"])

    assert result.exit_code == 0
    assert "reasoning" in result.stdout.lower()
    assert "governance" in result.stdout.lower()


def test_dedutive_inspect_smoke():
    from dedutive.cli import app

    result = runner.invoke(app, ["inspect", "configs/experiments/baseline_a.yaml", "--limit", "1"])

    assert result.exit_code == 0
    assert "Kepner-Tregoe" in result.stdout


def test_dedutive_evaluate_smoke():
    from dedutive.cli import app

    result = runner.invoke(app, ["evaluate", "--run", "tests/fixtures/sample_run.jsonl"])

    assert result.exit_code == 0
    assert "IDAUTH-001-kt" in result.stdout
    assert "100" in result.stdout


def test_dedutive_run_uses_experiment_strategy_in_rendered_prompt(monkeypatch, tmp_path):
    """Regression test: `dedutive run --experiment <path>` must actually apply the
    experiment's strategies to the generated prompt, not silently fall back to the
    scenario's legacy framework/governance_mode fields.

    Runs the same scenario under two experiment configs with different reasoning
    strategies (baseline_a: kepner_tregoe, baseline_b: recognition_primed) and
    asserts the resulting rendered system prompts differ and each names its own
    reasoning strategy.
    """
    import dedutive.cli as cli_module

    monkeypatch.setattr(cli_module, "OpenAICompatibleProvider", _RecordingStubProvider)

    def _run_once(experiment_path: str) -> str:
        _RecordingStubProvider.calls = []
        output_path = tmp_path / f"{Path(experiment_path).stem}.jsonl"
        result = runner.invoke(
            cli_module.app,
            [
                "run",
                "--experiment",
                experiment_path,
                "--limit",
                "1",
                "--model",
                "stub-model",
                "--output",
                str(output_path),
            ],
        )
        assert result.exit_code == 0, result.stdout
        assert len(_RecordingStubProvider.calls) == 1
        [messages] = _RecordingStubProvider.calls
        system_message = next(m["content"] for m in messages if m["role"] == "system")
        return system_message

    system_a = _run_once("configs/experiments/baseline_a.yaml")
    system_b = _run_once("configs/experiments/baseline_b.yaml")

    assert system_a != system_b
    assert "Kepner-Tregoe" in system_a
    assert "Recognition-Primed" in system_b or "recognition_primed" in system_b.lower()
    assert "Kepner-Tregoe" not in system_b
