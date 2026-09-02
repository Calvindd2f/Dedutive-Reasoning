from dedutive.data import load_cases, load_frameworks, load_tool_catalog
from dedutive.providers.base import GenerationResult


class _StubProvider:
    def generate(self, messages, *, model, temperature, response_format=None):
        return GenerationResult(
            text=(
                '{"problem_frame":"stub","known_facts":[],"key_unknowns":[],'
                '"hypotheses":[{"name":"stub","confidence":0.5,"why_it_fits":[]}],'
                '"next_best_tests":[],"decision":{"chosen_path":"stub","why":"stub","risks":[]},'
                '"execution_plan":["stub"],"verification_steps":[],'
                '"nits_brief":{"nature":"n","intention":"i","time":"t","special_instructions":"s"},'
                '"post_incident_learning":{"loop_type":"single_loop","lesson":"stub"}}'
            ),
            metadata={"provider": "stub"},
        )


def test_run_case_returns_run_record_from_relocated_runtime():
    from dedutive.orchestrator.runtime import run_case

    case = load_cases()[0]
    frameworks = load_frameworks()
    tools = load_tool_catalog()

    record = run_case(
        case,
        frameworks=frameworks,
        tool_catalog=tools,
        provider=_StubProvider(),
        model="stub-model",
    )

    assert record.case_id == case.case_id
    assert record.provider_metadata["provider"] == "stub"
