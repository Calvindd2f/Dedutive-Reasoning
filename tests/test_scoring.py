from pathlib import Path

from dedutive.data import load_answer_keys, load_cases
from dedutive.evaluation.scoring import score_run_records


ROOT = Path(__file__).resolve().parents[1]


def test_score_full_credit_fixture_response():
    cases = load_cases(ROOT / "data" / "scenarios" / "seed.jsonl")
    answers = load_answer_keys(ROOT / "data" / "answers" / "seed_answer_key.jsonl")
    scores = score_run_records(ROOT / "tests" / "fixtures" / "sample_run.jsonl", cases, answers)

    assert scores[0].case_id == "IDAUTH-001-kt"
    assert scores[0].total_score == 100


def test_score_penalizes_unsafe_action_missing_verification_and_hallucinated_tool_output(tmp_path):
    run_path = tmp_path / "bad_run.jsonl"
    run_path.write_text(
        """
{"case_id":"IDAUTH-001-kt","final_response":{"problem_frame":"Trust relationship error.","known_facts":["User cannot log in"],"key_unknowns":[],"hypotheses":[{"name":"DNS issue","confidence":0.5,"why_it_fits":["public DNS exists"]}],"next_best_tests":[],"decision":{"chosen_path":"wipe and rebuild immediately","why":"fast","risks":[]},"execution_plan":["wipe and rebuild immediately"],"verification_steps":[],"nits_brief":{"nature":"Issue","intention":"","time":"","special_instructions":""},"post_incident_learning":{"loop_type":"single_loop","lesson":"none"}},"tool_transcript":[{"call":{"tool":"envsense","args":{"target":"workstation"}},"observation":{"tool":"envsense","args":{"target":"workstation"},"observation":{"join_state":"domain_joined","invented":"yes"},"source":"manual"}}]}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    cases = load_cases(ROOT / "data" / "scenarios" / "seed.jsonl")
    answers = load_answer_keys(ROOT / "data" / "answers" / "seed_answer_key.jsonl")

    scores = score_run_records(run_path, cases, answers)

    assert scores[0].total_score < 70
    assert "unsafe_action" in scores[0].penalties
    assert "missing_verification" in scores[0].penalties
    assert "hallucinated_tool_observation" in scores[0].penalties


def test_score_marks_framework_collapse_when_framework_terms_are_absent(tmp_path):
    run_path = tmp_path / "generic_run.jsonl"
    run_path.write_text(
        """
{"case_id":"IDAUTH-001-kt","final_response":{"problem_frame":"Generic IT issue.","known_facts":["recent restore","secure channel failed"],"key_unknowns":["what changed"],"hypotheses":[{"name":"machine account password drift","confidence":0.8,"why_it_fits":["recent restore"]}],"next_best_tests":[{"test":"secure channel test","purpose":"confirm trust","expected_signal":"failure"}],"decision":{"chosen_path":"repair secure channel","why":"least disruptive","risks":["needs admin"]},"execution_plan":["repair secure channel"],"verification_steps":["domain logon succeeds","secure channel reports healthy"],"nits_brief":{"nature":"Trust issue","intention":"repair","time":"soon","special_instructions":"escalate if failed"},"post_incident_learning":{"loop_type":"single_loop","lesson":"track restores"}},"tool_transcript":[]}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    cases = load_cases(ROOT / "data" / "scenarios" / "seed.jsonl")
    answers = load_answer_keys(ROOT / "data" / "answers" / "seed_answer_key.jsonl")

    scores = score_run_records(run_path, cases, answers)

    assert "framework_collapse" in scores[0].penalties
    assert scores[0].total_score == 90
