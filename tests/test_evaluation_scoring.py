from pathlib import Path

from dedutive.data import load_answer_keys, load_cases


def test_score_run_records_relocated_behavior_matches_original():
    from dedutive.evaluation.scoring import score_run_records

    cases = load_cases()
    answers = load_answer_keys()
    scores = score_run_records(Path("tests/fixtures/sample_run.jsonl"), cases, answers)

    assert scores[0].case_id == "IDAUTH-001-kt"
    assert scores[0].total_score == 100
