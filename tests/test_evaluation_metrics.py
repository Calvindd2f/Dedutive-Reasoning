from pathlib import Path

from dedutive.data import load_answer_keys, load_cases


def test_compute_trajectory_metrics_from_score_breakdown():
    from dedutive.evaluation.metrics import compute_trajectory_metrics
    from dedutive.evaluation.scoring import score_run_records

    cases = load_cases()
    answers = load_answer_keys()
    scores = score_run_records(Path("tests/fixtures/sample_run.jsonl"), cases, answers)
    cases_by_id = {case.case_id: case for case in cases}

    metrics = compute_trajectory_metrics(scores[0], cases_by_id[scores[0].case_id])

    assert 0.0 <= metrics.root_cause_accuracy <= 1.0
    assert 0.0 <= metrics.unsafe_action_rate <= 1.0
    assert metrics.unsafe_action_rate == 0.0
    assert metrics.verification_success == 1.0
