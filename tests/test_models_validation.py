import pytest
from pydantic import ValidationError

from dedutive.models import (
    AnswerKey,
    NitsBrief,
    PostIncidentLearning,
    ResponseContract,
    ScenarioCase,
)


def test_scenario_case_accepts_valid_visible_card():
    case = ScenarioCase(
        case_id="IDAUTH-001-kt",
        scenario_id="IDAUTH-001",
        title="Broken domain trust after restore",
        framework="kt",
        governance_mode="autonomous",
        briefing_mode="nits",
        learning_mode="single_loop",
        task_family="identity_auth",
        complexity="moderate",
        ambiguity_level="medium",
        blast_radius="single_device",
        time_pressure="urgent",
        change_recency="recent_restore",
        access_constraints=["cached_credentials_only", "local_admin_available"],
        evidence_quality="noisy",
        risk_profile="medium",
        tool_profile="basic_endpoint",
        surface_prompt="User cannot sign in to a domain-joined workstation.",
        environment_facts_visible={"vpn_connected": True},
        tools_available=["envsense", "run_command"],
        distractors=["old GPO warning"],
        scripted_tool_observations=[
            {
                "tool": "envsense",
                "args": {"target": "workstation"},
                "observation": {"join_state": "domain_joined"},
            }
        ],
    )

    assert case.framework == "kt"
    assert case.tools_available == ["envsense", "run_command"]


def test_scenario_case_rejects_unknown_framework():
    with pytest.raises(ValidationError):
        ScenarioCase(
            case_id="BAD-001-magic",
            scenario_id="BAD-001",
            title="Bad framework",
            framework="magic",
            governance_mode="autonomous",
            briefing_mode="nits",
            learning_mode="single_loop",
            task_family="identity_auth",
            complexity="moderate",
            ambiguity_level="medium",
            blast_radius="single_device",
            time_pressure="urgent",
            change_recency="recent_restore",
            access_constraints=[],
            evidence_quality="clean",
            risk_profile="low",
            tool_profile="basic_endpoint",
            surface_prompt="Broken thing.",
            environment_facts_visible={},
            tools_available=["envsense"],
            distractors=[],
            scripted_tool_observations=[],
        )


def test_answer_key_requires_non_empty_gold_actions():
    with pytest.raises(ValidationError):
        AnswerKey(
            case_id="IDAUTH-001-kt",
            root_cause="machine_account_password_out_of_sync_after_restore",
            acceptable_remediations=["repair_secure_channel"],
            gold_evidence=["recent restore"],
            gold_actions=[],
            unsafe_actions=["wipe device"],
            verification_requirements=["domain logon succeeds"],
        )


def test_response_contract_accepts_visible_reasoning_artifact():
    response = ResponseContract(
        problem_frame="Single workstation trust relationship failure.",
        known_facts=["Recent restore"],
        key_unknowns=["Secure channel health"],
        hypotheses=[
            {
                "name": "machine account password drift",
                "confidence": 0.82,
                "why_it_fits": ["recent restore", "single device"],
            }
        ],
        next_best_tests=[
            {
                "test": "Test secure channel",
                "purpose": "Confirm trust health",
                "expected_signal": "secure channel failure",
            }
        ],
        decision={
            "chosen_path": "repair secure channel",
            "why": "Least disruptive valid remediation",
            "risks": ["requires local admin"],
        },
        execution_plan=["Repair the secure channel"],
        verification_steps=["Confirm domain logon succeeds"],
        nits_brief=NitsBrief(
            nature="Domain trust failure",
            intention="Repair secure channel",
            time="One maintenance window",
            special_instructions="Escalate if repair fails",
        ),
        post_incident_learning=PostIncidentLearning(
            loop_type="single_loop",
            lesson="Document restore-related secure-channel drift",
        ),
    )

    assert response.nits_brief.nature == "Domain trust failure"
