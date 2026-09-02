import json
from pathlib import Path

from dedutive.data import load_answer_keys, load_cases, load_frameworks, load_policies
from dedutive.evaluation.scoring import create_bandit_log_records, score_run_records


ROOT = Path(__file__).resolve().parents[1]


def test_create_bandit_log_records_emits_one_row_per_stage():
    cases = load_cases()
    answers = load_answer_keys()
    frameworks = load_frameworks()
    policies = load_policies(ROOT / "data" / "strategies" / "stage_policies.json", frameworks)
    scores = score_run_records(ROOT / "tests" / "fixtures" / "sample_policy_run.jsonl", cases, answers)

    records = create_bandit_log_records(scores, cases, policies)

    assert len(records) == 5
    assert records[0].policy_id == "baseline_a"
    assert records[0].case_id == "IDAUTH-001-kt"
    assert records[0].context.issue_family == "identity_auth"
    assert records[0].stage == "framing"
    assert records[0].chosen_arm == "grade"
    assert records[0].candidate_arms == ["safe", "grade", "3p", "generic"]
    assert 0.0 <= records[0].stage_reward.stage_reward <= 1.0
    assert records[0].final_score == 100


def test_bandit_log_records_are_json_serializable():
    cases = load_cases()
    answers = load_answer_keys()
    frameworks = load_frameworks()
    policies = load_policies(ROOT / "data" / "strategies" / "stage_policies.json", frameworks)
    scores = score_run_records(ROOT / "tests" / "fixtures" / "sample_policy_run.jsonl", cases, answers)

    row = create_bandit_log_records(scores, cases, policies)[0]

    assert json.loads(row.model_dump_json())["policy_id"] == "baseline_a"
