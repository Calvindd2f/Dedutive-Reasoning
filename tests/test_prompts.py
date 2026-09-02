from pathlib import Path

from dedutive.data import load_cases, load_frameworks, load_policies, load_tool_catalog
from dedutive.scenarios.prompts import render_prompt


ROOT = Path(__file__).resolve().parents[1]


def test_render_prompt_includes_framework_governance_tools_and_response_contract():
    case = load_cases(ROOT / "data" / "scenarios" / "seed.jsonl")[0]
    frameworks = load_frameworks(ROOT / "data" / "strategies" / "reasoning.json")
    tools = load_tool_catalog(ROOT / "data" / "tools" / "catalog.json")

    messages = render_prompt(case, frameworks, tools)
    rendered = "\n".join(message["content"] for message in messages)

    assert "Kepner-Tregoe" in rendered
    assert "governance mode" in rendered
    assert "envsense" in rendered
    assert "problem_frame" in rendered
    assert "nits_brief" in rendered


def test_render_prompt_with_policy_includes_all_stage_assignments():
    case = load_cases(ROOT / "data" / "scenarios" / "seed.jsonl")[0]
    frameworks = load_frameworks(ROOT / "data" / "strategies" / "reasoning.json")
    policies = load_policies(ROOT / "data" / "strategies" / "stage_policies.json", frameworks)
    tools = load_tool_catalog(ROOT / "data" / "tools" / "catalog.json")

    messages = render_prompt(case, frameworks, tools, policy=policies["baseline_a"])
    rendered = "\n".join(message["content"] for message in messages)

    assert "Stage assignment policy: baseline_a" in rendered
    assert "framing: GRADE" in rendered
    assert "hypothesis: Kepner-Tregoe" in rendered
    assert "check_selection: Kepner-Tregoe" in rendered
    assert "decision: FORDEC" in rendered
    assert "review: Single-loop learning" in rendered
    assert "stage_outputs" in rendered
