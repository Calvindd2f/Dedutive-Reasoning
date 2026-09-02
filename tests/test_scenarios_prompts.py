from dedutive.data import load_cases, load_frameworks, load_tool_catalog


def test_render_prompt_matches_existing_behavior():
    from dedutive.scenarios.prompts import render_prompt

    case = load_cases()[0]
    frameworks = load_frameworks()
    tools = load_tool_catalog()

    messages = render_prompt(case, frameworks, tools)

    assert messages[0]["role"] == "system"
    assert "Kepner-Tregoe" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert case.case_id in messages[1]["content"]


def test_render_session_prompt_uses_reasoning_strategy_stage_arms():
    from dedutive.decision.fordec import FordecStrategy
    from dedutive.communication.nits import NitsStrategy
    from dedutive.governance.vroom_yetton_jago import VroomYettonJagoStrategy
    from dedutive.learning.single_loop import SingleLoopStrategy
    from dedutive.orchestrator.session import TroubleshootingSession
    from dedutive.reasoning.kepner_tregoe import KepnerTregoeStrategy
    from dedutive.scenarios.prompts import render_session_prompt

    case = load_cases()[0]
    frameworks = load_frameworks()
    tools = load_tool_catalog()
    session = TroubleshootingSession(
        scenario=case,
        reasoning=KepnerTregoeStrategy(),
        governance=VroomYettonJagoStrategy(),
        decision=FordecStrategy(),
        communication=NitsStrategy(),
        learning=SingleLoopStrategy(),
    )

    messages = render_session_prompt(session, frameworks, tools)

    assert "Kepner-Tregoe" in messages[0]["content"]
    assert "FORDEC" in messages[0]["content"]
