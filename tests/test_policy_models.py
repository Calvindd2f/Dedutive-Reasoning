import pytest
from pydantic import ValidationError

from dedutive.models import AssignmentContext, StagePolicy, StageReward


def test_stage_policy_accepts_valid_stage_assignments():
    policy = StagePolicy(
        policy_id="baseline_a",
        description="GRADE framing, KT diagnosis, FORDEC decision.",
        stage_assignments={
            "framing": "grade",
            "hypothesis": "kt",
            "check_selection": "kt",
            "decision": "fordec",
            "review": "single_loop",
        },
    )

    assert policy.stage_assignments["decision"] == "fordec"


def test_stage_policy_rejects_unknown_stage():
    with pytest.raises(ValidationError, match="unknown stages"):
        StagePolicy(
            policy_id="bad_policy",
            description="Invalid stage.",
            stage_assignments={
                "framing": "grade",
                "hypothesis": "kt",
                "check_selection": "kt",
                "decision": "fordec",
                "review": "single_loop",
                "extra": "kt",
            },
        )


def test_stage_policy_rejects_arm_that_is_invalid_for_stage():
    with pytest.raises(ValidationError, match="invalid arm"):
        StagePolicy(
            policy_id="bad_policy",
            description="Wrong arm for stage.",
            stage_assignments={
                "framing": "fordec",
                "hypothesis": "kt",
                "check_selection": "kt",
                "decision": "fordec",
                "review": "single_loop",
            },
        )


def test_assignment_context_is_derived_from_case():
    from dedutive.data import load_cases

    case = load_cases()[0]
    context = AssignmentContext.from_case(case)

    assert context.issue_family == "identity_auth"
    assert context.ambiguity == "medium"
    assert context.access_level == "cached_only"
    assert context.recent_change is True
    assert context.user_impact == "high"


def test_stage_reward_accepts_stage_local_components():
    reward = StageReward(
        framing_quality=0.8,
        hypothesis_quality=0.7,
        check_selection_quality=0.6,
        decision_quality=0.9,
        verification_quality=1.0,
        risk_discipline=0.75,
        efficiency_penalty=0.0,
        hallucination_penalty=0.0,
        stage_reward=0.82,
    )

    assert reward.stage_reward == 0.82
