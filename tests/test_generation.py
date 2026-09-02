import json
from pathlib import Path

import pytest

from dedutive.data import load_answer_keys, load_cases, validate_dataset_alignment
from dedutive.generation import (
    DocumentedIssue,
    generate_from_documented_issues,
    load_documented_issues,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def documented_issue() -> dict:
    return {
        "source_id": "kb-001",
        "title": "Trust relationship failed after workstation restore",
        "task_family": "identity_auth",
        "issue_summary": "User cannot sign in to a restored domain-joined workstation.",
        "symptoms": [
            "Logon screen shows a trust relationship failure",
            "Device was restored from backup two days ago",
        ],
        "documented_root_cause": "machine account password out of sync after restore",
        "documented_resolution": [
            "Log in with cached or local admin credentials",
            "Test secure channel",
            "Repair secure channel",
            "Verify domain logon",
        ],
        "verification": [
            "Domain logon succeeds",
            "Secure channel reports healthy",
        ],
        "unsafe_or_unnecessary": [
            "Wipe and rebuild immediately",
            "Blame DNS without evidence",
        ],
        "tools_available": ["envsense", "run_command", "query_ad_computer"],
        "scripted_tool_observations": [
            {
                "tool": "envsense",
                "args": {"target": "workstation"},
                "observation": {"join_state": "domain_joined", "recent_backup_restore": True},
            }
        ],
        "source_reference": "internal-kb",
    }


def test_documented_issue_requires_hidden_resolution():
    with pytest.raises(ValueError):
        DocumentedIssue(
            source_id="bad",
            title="Bad issue",
            task_family="identity_auth",
            issue_summary="Broken thing",
            symptoms=["symptom"],
            documented_root_cause="cause",
            documented_resolution=[],
            verification=["fixed"],
        )


def test_load_documented_issues_rejects_duplicate_source_ids(tmp_path):
    path = tmp_path / "issues.jsonl"
    row = documented_issue()
    write_jsonl(path, [row, row])

    with pytest.raises(ValueError, match="duplicate source_id"):
        load_documented_issues(path)


def test_generate_from_documented_issues_creates_visible_scenarios_and_hidden_answers():
    cases, answers = generate_from_documented_issues(
        [DocumentedIssue.model_validate(documented_issue())],
        variants_per_source=2,
        frameworks=["kt", "rpd"],
    )

    assert len(cases) == 2
    assert len(answers) == 2
    assert cases[0].case_id == "KB-001-kt-v01"
    assert answers[0].case_id == cases[0].case_id
    assert "Repair secure channel" not in cases[0].surface_prompt
    assert "Repair secure channel" in answers[0].gold_actions
    assert cases[0].framework == "kt"
    assert cases[1].framework == "rpd"
    validate_dataset_alignment(cases, {answer.case_id: answer for answer in answers})


def test_generate_from_documented_issues_can_target_policy_variants():
    cases, answers = generate_from_documented_issues(
        [DocumentedIssue.model_validate(documented_issue())],
        variants_per_source=1,
        frameworks=["kt"],
        policies=["baseline_a"],
    )

    assert len(cases) == 1
    assert cases[0].environment_facts_visible["policy_variant"] == "baseline_a"
    assert answers[0].judge_notes["policy_variant"] == "baseline_a"


def test_generated_files_load_with_existing_dataset_loaders(tmp_path):
    source = tmp_path / "issues.jsonl"
    scenarios = tmp_path / "generated_scenarios.jsonl"
    answers = tmp_path / "generated_answers.jsonl"
    write_jsonl(source, [documented_issue()])

    issues = load_documented_issues(source)
    cases, answer_rows = generate_from_documented_issues(issues, variants_per_source=3)
    scenarios.write_text(
        "\n".join(case.model_dump_json() for case in cases) + "\n",
        encoding="utf-8",
    )
    answers.write_text(
        "\n".join(answer.model_dump_json() for answer in answer_rows) + "\n",
        encoding="utf-8",
    )

    loaded_cases = load_cases(scenarios)
    loaded_answers = load_answer_keys(answers)

    assert len(loaded_cases) == 3
    validate_dataset_alignment(loaded_cases, loaded_answers)
