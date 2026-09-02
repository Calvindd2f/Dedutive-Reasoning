from __future__ import annotations

import json
import re
from typing import Any

from dedutive.models import RunRecord, ScenarioCase, StagePolicy, ToolCall, ToolInteraction
from dedutive.scenarios.prompts import render_prompt
from dedutive.providers.base import Provider
from dedutive.tools import ToolCatalog, ToolSimulationError, ToolSimulator


def parse_json_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    return json.loads(stripped)


def run_case(
    case: ScenarioCase,
    *,
    frameworks: dict[str, Any],
    tool_catalog: ToolCatalog,
    provider: Provider,
    model: str,
    policy: StagePolicy | None = None,
    temperature: float = 0.0,
    max_turns: int = 4,
) -> RunRecord:
    messages = render_prompt(case, frameworks, tool_catalog, policy=policy)
    simulator = ToolSimulator(
        available_tools=case.tools_available,
        scripted_observations=case.scripted_tool_observations,
        catalog=tool_catalog,
    )
    transcript: list[ToolInteraction] = []
    provider_metadata: dict[str, Any] = {}

    for _ in range(max_turns):
        result = provider.generate(
            messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        provider_metadata = result.metadata
        payload = parse_json_text(result.text)
        if policy is not None:
            provider_metadata["policy_id"] = policy.policy_id
        tool_request = payload.get("tool_request")
        if tool_request is None:
            return RunRecord(case_id=case.case_id, final_response=payload, tool_transcript=transcript, provider_metadata=provider_metadata)

        call = ToolCall.model_validate(tool_request)
        try:
            observation = simulator.invoke(call)
            transcript.append(ToolInteraction(call=call, observation=observation))
            messages.append({"role": "assistant", "content": json.dumps({"tool_request": call.model_dump()})})
            messages.append({"role": "tool", "content": observation.model_dump_json()})
        except ToolSimulationError as exc:
            transcript.append(ToolInteraction(call=call, error=str(exc)))
            messages.append({"role": "tool", "content": json.dumps({"error": str(exc)})})

    raise RuntimeError(f"case {case.case_id} exceeded max investigation turns ({max_turns})")
