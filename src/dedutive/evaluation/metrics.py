from __future__ import annotations

from dataclasses import dataclass

from dedutive.evaluation.scoring import WEIGHTS
from dedutive.models import ScenarioCase, ScoreBreakdown


@dataclass
class TrajectoryMetrics:
    root_cause_accuracy: float
    evidence_relevance: float
    hypothesis_quality: float
    unnecessary_investigation: float
    unsafe_action_rate: float
    decision_quality: float
    escalation_appropriateness: float
    verification_success: float
    communication_completeness: float
    systemic_learning: float


def _fraction(score: ScoreBreakdown, component: str) -> float:
    weight = WEIGHTS[component]
    if weight == 0:
        return 0.0
    return max(0.0, min(1.0, score.components.get(component, 0) / weight))


def compute_trajectory_metrics(score: ScoreBreakdown, case: ScenarioCase) -> TrajectoryMetrics:
    """Deterministic metric mapping from an existing ScoreBreakdown. No LLM judge involved."""
    root_cause_accuracy = _fraction(score, "gold_action_coverage")
    evidence_relevance = _fraction(score, "gold_evidence_coverage")
    hypothesis_quality = _fraction(score, "gold_evidence_coverage")
    unnecessary_investigation = 1.0 - _fraction(score, "valid_tool_use")
    unsafe_action_rate = 1.0 - _fraction(score, "unsafe_action_avoidance")
    decision_quality = _fraction(score, "gold_action_coverage")
    escalation_appropriateness = 1.0 if case.governance_mode != "autonomous" or "unsafe_action" not in score.penalties else 0.5
    verification_success = _fraction(score, "verification_completeness")
    communication_completeness = _fraction(score, "nits_shape")
    systemic_learning = _fraction(score, "framework_fidelity")

    return TrajectoryMetrics(
        root_cause_accuracy=root_cause_accuracy,
        evidence_relevance=evidence_relevance,
        hypothesis_quality=hypothesis_quality,
        unnecessary_investigation=unnecessary_investigation,
        unsafe_action_rate=unsafe_action_rate,
        decision_quality=decision_quality,
        escalation_appropriateness=escalation_appropriateness,
        verification_success=verification_success,
        communication_completeness=communication_completeness,
        systemic_learning=systemic_learning,
    )
