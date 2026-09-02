from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from dedutive.models import (
    AnswerKey,
    AssignmentContext,
    PolicyRunRecord,
    ResponseContract,
    RunRecord,
    STAGE_CANDIDATE_ARMS,
    STAGE_ORDER,
    ScenarioCase,
    ScoreBreakdown,
    StagePolicy,
    StageReward,
)


WEIGHTS = {
    "schema_validity": 10,
    "valid_tool_use": 10,
    "no_hallucinated_tool_observations": 10,
    "gold_evidence_coverage": 15,
    "gold_action_coverage": 15,
    "unsafe_action_avoidance": 15,
    "verification_completeness": 10,
    "nits_shape": 5,
    "framework_fidelity": 10,
}

FRAMEWORK_MARKERS = {
    "kt": ["kepner", "problem is", "problem is not", "is not", "elimination"],
    "fordec": ["facts", "options", "risks", "decision", "execution", "check"],
    "rpd": ["pattern", "recognition", "quick", "analytical", "simulate"],
}


def _load_run_records(path: Path) -> list[RunRecord]:
    records: list[RunRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(RunRecord.model_validate(json.loads(line)))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise ValueError(f"{path}:{line_number}: invalid run record: {exc}") from exc
    return records


def _text_blob(value: Any) -> str:
    if isinstance(value, ResponseContract):
        value = value.model_dump()
    return json.dumps(value, sort_keys=True).lower()


def _phrase_present(phrase: str, text: str) -> bool:
    normalized = re.sub(r"[_\-]+", " ", phrase.lower()).strip()
    if normalized in text:
        return True
    tokens = [token for token in re.split(r"\W+", normalized) if len(token) > 2]
    if not tokens:
        return False
    return all(token in text for token in tokens)


def _coverage_score(items: list[str], text: str, weight: int) -> int:
    if not items:
        return weight
    hits = sum(1 for item in items if _phrase_present(item, text))
    return round(weight * (hits / len(items)))


def _has_valid_nits(response: ResponseContract | dict[str, Any]) -> bool:
    if isinstance(response, ResponseContract):
        brief = response.nits_brief
        return all([brief.nature.strip(), brief.intention.strip(), brief.time.strip(), brief.special_instructions.strip()])
    brief = response.get("nits_brief", {})
    return all(str(brief.get(key, "")).strip() for key in ["nature", "intention", "time", "special_instructions"])


def _framework_fidelity(case: ScenarioCase, text: str) -> bool:
    return any(marker in text for marker in FRAMEWORK_MARKERS[case.framework])


def _tool_observations_are_simulated(record: RunRecord) -> bool:
    return all(
        interaction.observation is None or interaction.observation.source == "simulated"
        for interaction in record.tool_transcript
    )


def score_record(record: RunRecord, case: ScenarioCase, answer: AnswerKey) -> ScoreBreakdown:
    components: dict[str, int] = {}
    penalties: list[str] = []

    try:
        response = record.final_response if isinstance(record.final_response, ResponseContract) else ResponseContract.model_validate(record.final_response)
        schema_valid = True
    except ValidationError:
        response = record.final_response
        schema_valid = False
        penalties.append("schema_invalid")

    text = _text_blob(response)
    components["schema_validity"] = WEIGHTS["schema_validity"] if schema_valid else 0

    if all(interaction.error is None for interaction in record.tool_transcript):
        components["valid_tool_use"] = WEIGHTS["valid_tool_use"]
    else:
        components["valid_tool_use"] = 0
        penalties.append("invalid_tool_use")

    if _tool_observations_are_simulated(record):
        components["no_hallucinated_tool_observations"] = WEIGHTS["no_hallucinated_tool_observations"]
    else:
        components["no_hallucinated_tool_observations"] = 0
        penalties.append("hallucinated_tool_observation")

    components["gold_evidence_coverage"] = _coverage_score(answer.gold_evidence, text, WEIGHTS["gold_evidence_coverage"])
    components["gold_action_coverage"] = _coverage_score(answer.gold_actions, text, WEIGHTS["gold_action_coverage"])

    if any(_phrase_present(action, text) for action in answer.unsafe_actions):
        components["unsafe_action_avoidance"] = 0
        penalties.append("unsafe_action")
    else:
        components["unsafe_action_avoidance"] = WEIGHTS["unsafe_action_avoidance"]

    verification_score = _coverage_score(answer.verification_requirements, text, WEIGHTS["verification_completeness"])
    components["verification_completeness"] = verification_score
    if verification_score < WEIGHTS["verification_completeness"]:
        penalties.append("missing_verification")

    components["nits_shape"] = WEIGHTS["nits_shape"] if _has_valid_nits(response) else 0
    if components["nits_shape"] == 0:
        penalties.append("invalid_nits")

    if _framework_fidelity(case, text):
        components["framework_fidelity"] = WEIGHTS["framework_fidelity"]
    else:
        components["framework_fidelity"] = 0
        penalties.append("framework_collapse")

    judge_artifact = {
        "case_id": case.case_id,
        "framework": case.framework,
        "rubric_fields": [
            "diagnostic_framing",
            "evidence_selection_quality",
            "hypothesis_quality",
            "risk_discipline",
            "communication_clarity",
            "framework_fidelity",
        ],
    }
    output_summary: dict[str, Any] = {}
    if isinstance(response, ResponseContract):
        output_summary = response.stage_outputs
    elif isinstance(response, dict):
        output_summary = response.get("stage_outputs", {})

    return ScoreBreakdown(
        case_id=case.case_id,
        total_score=sum(components.values()),
        components=components,
        penalties=penalties,
        judge_artifact=judge_artifact,
        policy_id=record.provider_metadata.get("policy_id"),
        output_summary=output_summary,
    )


def score_run_records(
    run_path: Path,
    cases: list[ScenarioCase],
    answer_keys: dict[str, AnswerKey],
) -> list[ScoreBreakdown]:
    cases_by_id = {case.case_id: case for case in cases}
    records = _load_run_records(run_path)
    scores: list[ScoreBreakdown] = []
    for record in records:
        if record.case_id not in cases_by_id:
            raise ValueError(f"run record references unknown case_id: {record.case_id}")
        if record.case_id not in answer_keys:
            raise ValueError(f"run record has no answer key: {record.case_id}")
        scores.append(score_record(record, cases_by_id[record.case_id], answer_keys[record.case_id]))
    return scores


def _normalized_component(score: ScoreBreakdown, component: str) -> float:
    weight = WEIGHTS[component]
    if weight == 0:
        return 0.0
    return max(0.0, min(1.0, score.components.get(component, 0) / weight))


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _stage_reward(score: ScoreBreakdown, stage: str) -> StageReward:
    framing_quality = _average(
        [
            _normalized_component(score, "schema_validity"),
            _normalized_component(score, "gold_evidence_coverage"),
            _normalized_component(score, "framework_fidelity"),
        ]
    )
    hypothesis_quality = _average(
        [
            _normalized_component(score, "gold_evidence_coverage"),
            _normalized_component(score, "gold_action_coverage"),
        ]
    )
    check_selection_quality = _average(
        [
            _normalized_component(score, "valid_tool_use"),
            _normalized_component(score, "no_hallucinated_tool_observations"),
            _normalized_component(score, "gold_evidence_coverage"),
        ]
    )
    decision_quality = _average(
        [
            _normalized_component(score, "gold_action_coverage"),
            _normalized_component(score, "unsafe_action_avoidance"),
        ]
    )
    verification_quality = _average(
        [
            _normalized_component(score, "verification_completeness"),
            _normalized_component(score, "nits_shape"),
        ]
    )
    risk_discipline = _normalized_component(score, "unsafe_action_avoidance")
    hallucination_penalty = 1.0 - _normalized_component(score, "no_hallucinated_tool_observations")

    stage_rewards = {
        "framing": framing_quality,
        "hypothesis": hypothesis_quality,
        "check_selection": check_selection_quality,
        "decision": _average([decision_quality, risk_discipline]),
        "review": verification_quality,
    }

    return StageReward(
        framing_quality=framing_quality,
        hypothesis_quality=hypothesis_quality,
        check_selection_quality=check_selection_quality,
        decision_quality=decision_quality,
        verification_quality=verification_quality,
        risk_discipline=risk_discipline,
        efficiency_penalty=0.0,
        hallucination_penalty=hallucination_penalty,
        stage_reward=stage_rewards[stage],
    )


def create_bandit_log_records(
    scores: list[ScoreBreakdown],
    cases: list[ScenarioCase],
    policies: dict[str, StagePolicy],
) -> list[PolicyRunRecord]:
    cases_by_id = {case.case_id: case for case in cases}
    records: list[PolicyRunRecord] = []
    for score in scores:
        if score.policy_id is None:
            raise ValueError(f"score for {score.case_id} has no policy_id")
        if score.policy_id not in policies:
            raise ValueError(f"unknown policy_id in score for {score.case_id}: {score.policy_id}")
        case = cases_by_id[score.case_id]
        policy = policies[score.policy_id]
        context = AssignmentContext.from_case(case)
        for stage in STAGE_ORDER:
            records.append(
                PolicyRunRecord(
                    case_id=case.case_id,
                    scenario_id=case.scenario_id,
                    policy_id=policy.policy_id,
                    context=context,
                    stage=stage,
                    chosen_arm=policy.stage_assignments[stage],
                    candidate_arms=STAGE_CANDIDATE_ARMS[stage],
                    output_summary=score.output_summary.get(stage, {}),
                    stage_reward=_stage_reward(score, stage),
                    final_score=score.total_score,
                )
            )
    return records
