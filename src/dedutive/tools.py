from __future__ import annotations

from pydantic import BaseModel

from .models import ScriptedToolObservation, ToolCall, ToolDefinition, ToolObservation


class ToolSimulationError(ValueError):
    pass


class ToolCatalog(BaseModel):
    definitions: dict[str, ToolDefinition]

    @classmethod
    def from_rows(cls, rows: list[dict]) -> "ToolCatalog":
        definitions = [ToolDefinition.model_validate(row) for row in rows]
        return cls(definitions={definition.name: definition for definition in definitions})

    def require(self, tool_name: str) -> ToolDefinition:
        try:
            return self.definitions[tool_name]
        except KeyError as exc:
            raise ToolSimulationError(f"unknown tool: {tool_name}") from exc


class ToolSimulator:
    def __init__(
        self,
        *,
        available_tools: list[str],
        scripted_observations: list[dict | ScriptedToolObservation],
        catalog: ToolCatalog,
    ) -> None:
        self.available_tools = set(available_tools)
        self.catalog = catalog
        self.scripted_observations = [
            row if isinstance(row, ScriptedToolObservation) else ScriptedToolObservation.model_validate(row)
            for row in scripted_observations
        ]

    def invoke(self, call: ToolCall) -> ToolObservation:
        if call.tool not in self.available_tools:
            raise ToolSimulationError(f"tool is not available for this case: {call.tool}")

        definition = self.catalog.require(call.tool)
        missing_args = [arg for arg in definition.required_args if arg not in call.args]
        if missing_args:
            raise ToolSimulationError(
                f"{call.tool} missing required args: {', '.join(sorted(missing_args))}"
            )

        for scripted in self.scripted_observations:
            if scripted.tool == call.tool and scripted.args == call.args:
                return ToolObservation(
                    tool=scripted.tool,
                    args=scripted.args,
                    observation=scripted.observation,
                    source="simulated",
                )

        raise ToolSimulationError(f"no scripted observation for {call.tool} with args {call.args}")
