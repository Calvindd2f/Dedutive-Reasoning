import json
from pathlib import Path

import pytest

from dedutive.data import load_answer_keys, load_cases, validate_dataset_alignment


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def valid_case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "scenario_id": "IDAUTH-001",
        "title": "Broken domain trust after restore",
        "framework": "kt",
        "governance_mode": "autonomous",
        "briefing_mode": "nits",
        "learning_mode": "single_loop",
        "task_family": "identity_auth",
        "complexity": "moderate",
        "ambiguity_level": "medium",
        "blast_radius": "single_device",
        "time_pressure": "urgent",
        "change_recency": "recent_restore",
        "access_constraints": ["cached_credentials_only"],
        "evidence_quality": "noisy",
        "risk_profile": "medium",
        "tool_profile": "basic_endpoint",
        "surface_prompt": "User cannot sign in.",
        "environment_facts_visible": {"recent_backup_restore": True},
        "tools_available": ["envsense"],
        "distractors": ["old GPO warning"],
        "scripted_tool_observations": [
            {
                "tool": "envsense",
                "args": {"target": "workstation"},
                "observation": {"join_state": "domain_joined"},
            }
        ],
    }


def valid_answer(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "root_cause": "machine_account_password_out_of_sync_after_restore",
        "acceptable_remediations": ["repair_secure_channel"],
        "gold_evidence": ["recent restore", "secure channel"],
        "gold_actions": ["repair secure channel"],
        "unsafe_actions": ["wipe and rebuild immediately"],
        "verification_requirements": ["domain logon succeeds"],
    }


def test_validate_dataset_alignment_accepts_matching_files(tmp_path):
    scenarios = tmp_path / "scenarios.jsonl"
    answers = tmp_path / "answers.jsonl"
    write_jsonl(scenarios, [valid_case("IDAUTH-001-kt")])
    write_jsonl(answers, [valid_answer("IDAUTH-001-kt")])

    cases = load_cases(scenarios)
    answer_keys = load_answer_keys(answers)

    validate_dataset_alignment(cases, answer_keys)


def test_validate_dataset_alignment_rejects_missing_answer_key(tmp_path):
    scenarios = tmp_path / "scenarios.jsonl"
    answers = tmp_path / "answers.jsonl"
    write_jsonl(scenarios, [valid_case("IDAUTH-001-kt")])
    write_jsonl(answers, [])

    with pytest.raises(ValueError, match="missing answer keys"):
        validate_dataset_alignment(load_cases(scenarios), load_answer_keys(answers))


def test_load_cases_rejects_duplicate_case_ids(tmp_path):
    scenarios = tmp_path / "scenarios.jsonl"
    write_jsonl(scenarios, [valid_case("IDAUTH-001-kt"), valid_case("IDAUTH-001-kt")])

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_cases(scenarios)
