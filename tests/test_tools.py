import pytest

from dedutive.models import ToolCall
from dedutive.tools import ToolCatalog, ToolSimulationError, ToolSimulator


def test_tool_simulator_returns_scripted_observation():
    catalog = ToolCatalog.from_rows(
        [
            {
                "name": "envsense",
                "description": "Read environment facts",
                "required_args": ["target"],
                "returns": ["join_state"],
            }
        ]
    )
    simulator = ToolSimulator(
        available_tools=["envsense"],
        scripted_observations=[
            {
                "tool": "envsense",
                "args": {"target": "workstation"},
                "observation": {"join_state": "domain_joined"},
            }
        ],
        catalog=catalog,
    )

    observation = simulator.invoke(ToolCall(tool="envsense", args={"target": "workstation"}))

    assert observation.observation == {"join_state": "domain_joined"}
    assert observation.source == "simulated"


def test_tool_simulator_rejects_unavailable_tool():
    catalog = ToolCatalog.from_rows(
        [
            {
                "name": "envsense",
                "description": "Read environment facts",
                "required_args": ["target"],
                "returns": ["join_state"],
            }
        ]
    )
    simulator = ToolSimulator(available_tools=[], scripted_observations=[], catalog=catalog)

    with pytest.raises(ToolSimulationError, match="not available"):
        simulator.invoke(ToolCall(tool="envsense", args={"target": "workstation"}))


def test_tool_simulator_rejects_missing_required_arg():
    catalog = ToolCatalog.from_rows(
        [
            {
                "name": "envsense",
                "description": "Read environment facts",
                "required_args": ["target"],
                "returns": ["join_state"],
            }
        ]
    )
    simulator = ToolSimulator(available_tools=["envsense"], scripted_observations=[], catalog=catalog)

    with pytest.raises(ToolSimulationError, match="missing required args"):
        simulator.invoke(ToolCall(tool="envsense", args={}))
