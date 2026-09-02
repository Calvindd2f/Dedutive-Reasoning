def test_dedutive_models_importable():
    from dedutive.models import ScenarioCase, StagePolicy, STAGE_ORDER

    assert STAGE_ORDER == ("framing", "hypothesis", "check_selection", "decision", "review")


def test_dedutive_providers_importable():
    from dedutive.providers.base import Provider, GenerationResult
    from dedutive.providers.openai_compatible import OpenAICompatibleProvider

    assert OpenAICompatibleProvider.__name__ == "OpenAICompatibleProvider"


def test_dedutive_tools_importable():
    from dedutive.tools import ToolCatalog, ToolSimulator, ToolSimulationError

    assert ToolSimulationError.__mro__[1] is ValueError
