from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from dedutive.models import AssignmentContext, ScenarioCase, StagePolicy
from dedutive.tools import ToolCatalog

if TYPE_CHECKING:
    from dedutive.orchestrator.session import TroubleshootingSession


def render_prompt(
    case: ScenarioCase,
    frameworks: dict[str, Any],
    tool_catalog: ToolCatalog,
    policy: StagePolicy | None = None,
) -> list[dict[str, str]]:
    framework = frameworks["frameworks"][case.framework]
    governance = frameworks["governance_modes"][case.governance_mode]
    response_contract = frameworks["response_contract"]
    tools = [
        tool_catalog.definitions[name].model_dump()
        for name in case.tools_available
        if name in tool_catalog.definitions
    ]

    system_parts = [
        "You are an IT incident RCA benchmark solver.",
        "Use visible structured reasoning artifacts only; do not output hidden chain-of-thought.",
        "Do not invent tool results. Request tools only through JSON tool_request objects.",
        "Do not skip verification.",
    ]
    if policy is None:
        system_parts.extend([f"Framework: {framework['name']}", framework["adapter"]])
    else:
        stage_arms = frameworks["stage_arms"]
        system_parts.append(f"Stage assignment policy: {policy.policy_id}")
        system_parts.append(policy.description)
        system_parts.append("Apply these stage assignments in order:")
        for assignment in policy.assignments():
            arm = stage_arms[assignment.chosen_arm]
            system_parts.append(f"{assignment.stage}: {arm['name']} - {arm['adapter']}")
    system_parts.extend(
        [
            f"governance mode: {case.governance_mode} - {governance}",
            "Final response must be valid JSON matching this response contract:",
            json.dumps(response_contract, indent=2),
        ]
    )
    system = "\n".join(system_parts)

    user = "\n".join(
        [
            f"Case ID: {case.case_id}",
            f"Title: {case.title}",
            f"Task family: {case.task_family}",
            f"Complexity: {case.complexity}",
            f"Surface prompt: {case.surface_prompt}",
            "Visible environment facts:",
            json.dumps(case.environment_facts_visible, indent=2, sort_keys=True),
            "Assignment context:",
            AssignmentContext.from_case(case).model_dump_json(indent=2),
            "Distractors that may or may not matter:",
            json.dumps(case.distractors, indent=2),
            "Available deterministic tools:",
            json.dumps(tools, indent=2, sort_keys=True),
            "If you need evidence, output exactly:",
            '{"tool_request":{"tool":"tool_name","args":{"arg":"value"}}}',
            "When ready, output the final JSON response contract.",
        ]
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def session_to_stage_policy(session: "TroubleshootingSession") -> StagePolicy:
    stage_assignments = dict(session.reasoning.stage_arms())
    stage_assignments.setdefault("decision", "fordec")
    stage_assignments.setdefault("review", session.learning.loop_type)
    return StagePolicy(
        policy_id=f"session::{session.reasoning.name}+{session.decision.name}+{session.learning.name}",
        description=(
            f"{session.reasoning.name} reasoning, {session.governance.name} governance, "
            f"{session.decision.name} decision, {session.communication.name} communication, "
            f"{session.learning.name} learning."
        ),
        stage_assignments=stage_assignments,
    )


def render_session_prompt(
    session: "TroubleshootingSession",
    frameworks: dict[str, Any],
    tool_catalog: ToolCatalog,
) -> list[dict[str, str]]:
    policy = session_to_stage_policy(session)
    return render_prompt(session.scenario, frameworks, tool_catalog, policy=policy)
