from typer.testing import CliRunner

from deductive_rca_bench.cli import app


runner = CliRunner()


def test_validate_cli_smoke():
    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "30 cases" in result.stdout


def test_render_prompts_cli_smoke():
    result = runner.invoke(app, ["render-prompts", "--limit", "1"])

    assert result.exit_code == 0
    assert "IDAUTH-001-kt" in result.stdout
    assert "Kepner-Tregoe" in result.stdout


def test_policies_cli_smoke():
    result = runner.invoke(app, ["policies"])

    assert result.exit_code == 0
    assert "baseline_a" in result.stdout
    assert "generic_baseline" in result.stdout


def test_validate_cli_accepts_policy_file():
    result = runner.invoke(app, ["validate", "--policies", "data/strategies/stage_policies.json"])

    assert result.exit_code == 0
    assert "4 policies" in result.stdout


def test_render_prompts_cli_accepts_policy():
    result = runner.invoke(app, ["render-prompts", "--policy", "baseline_a", "--limit", "1"])

    assert result.exit_code == 0
    assert "Stage assignment policy: baseline_a" in result.stdout
    assert "framing: GRADE" in result.stdout


def test_score_cli_smoke():
    result = runner.invoke(app, ["score", "--run", "tests/fixtures/sample_run.jsonl"])

    assert result.exit_code == 0
    assert "IDAUTH-001-kt" in result.stdout
    assert "100" in result.stdout


def test_score_cli_writes_bandit_log(tmp_path):
    output = tmp_path / "bandit_log.jsonl"
    result = runner.invoke(
        app,
        [
            "score",
            "--run",
            "tests/fixtures/sample_policy_run.jsonl",
            "--bandit-log",
            str(output),
        ],
    )

    assert result.exit_code == 0
    rows = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 5
    assert "baseline_a" in rows[0]


def test_generate_from_docs_cli_writes_scenarios_and_answers(tmp_path):
    source = tmp_path / "issues.jsonl"
    scenarios = tmp_path / "generated_scenarios.jsonl"
    answers = tmp_path / "generated_answers.jsonl"
    source.write_text(
        """
{"source_id":"kb-001","title":"Trust relationship failed after restore","task_family":"identity_auth","issue_summary":"User cannot sign in to a restored domain-joined workstation.","symptoms":["Trust relationship failure at logon","Device restored from backup two days ago"],"documented_root_cause":"machine account password out of sync after restore","documented_resolution":["Log in with cached or local admin credentials","Test secure channel","Repair secure channel","Verify domain logon"],"verification":["Domain logon succeeds","Secure channel reports healthy"],"unsafe_or_unnecessary":["Wipe and rebuild immediately","Blame DNS without evidence"],"tools_available":["envsense","run_command"],"scripted_tool_observations":[{"tool":"envsense","args":{"target":"workstation"},"observation":{"join_state":"domain_joined"}}],"source_reference":"internal-kb"}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "generate-from-docs",
            "--source",
            str(source),
            "--output-scenarios",
            str(scenarios),
            "--output-answers",
            str(answers),
            "--variants-per-source",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Generated 2 scenarios and 2 answer keys" in result.stdout
    assert scenarios.exists()
    assert answers.exists()
    assert "Repair secure channel" not in scenarios.read_text(encoding="utf-8")
    assert "Repair secure channel" in answers.read_text(encoding="utf-8")


from dedutive.cli import app as dedutive_app


def test_dedutive_scenario_validate_cli_smoke():
    result = runner.invoke(dedutive_app, ["scenario", "validate"])

    assert result.exit_code == 0
    assert "30 cases" in result.stdout


def test_dedutive_evaluate_cli_smoke():
    result = runner.invoke(dedutive_app, ["evaluate", "--run", "tests/fixtures/sample_run.jsonl"])

    assert result.exit_code == 0
    assert "IDAUTH-001-kt" in result.stdout
    assert "100" in result.stdout
