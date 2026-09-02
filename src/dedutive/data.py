from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, TypeVar

from pydantic import BaseModel, ValidationError

from .models import AnswerKey, ScenarioCase, StagePolicy, ToolDefinition
from .tools import ToolCatalog


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCENARIOS = ROOT / "data" / "scenarios" / "seed.jsonl"
DEFAULT_ANSWERS = ROOT / "data" / "answers" / "seed_answer_key.jsonl"
DEFAULT_REASONING_STRATEGIES = ROOT / "data" / "strategies" / "reasoning.json"
DEFAULT_TOOL_CATALOG = ROOT / "data" / "tools" / "catalog.json"
DEFAULT_STAGE_POLICIES = ROOT / "data" / "strategies" / "stage_policies.json"

# backwards-compat aliases for the legacy shim (Task 8)
DEFAULT_FRAMEWORKS = DEFAULT_REASONING_STRATEGIES
DEFAULT_POLICIES = DEFAULT_STAGE_POLICIES

T = TypeVar("T", bound=BaseModel)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _validate_rows(path: Path, rows: list[dict[str, Any]], model: type[T]) -> list[T]:
    validated: list[T] = []
    for index, row in enumerate(rows, start=1):
        try:
            validated.append(model.model_validate(row))
        except ValidationError as exc:
            raise ValueError(f"{path}:{index}: {model.__name__} validation failed: {exc}") from exc
    return validated


def _reject_duplicate_ids(items: Iterable[BaseModel], attr: str) -> None:
    seen: set[str] = set()
    for item in items:
        value = getattr(item, attr)
        if value in seen:
            raise ValueError(f"duplicate {attr}: {value}")
        seen.add(value)


def load_cases(path: Path = DEFAULT_SCENARIOS) -> list[ScenarioCase]:
    cases = _validate_rows(path, read_jsonl(path), ScenarioCase)
    _reject_duplicate_ids(cases, "case_id")
    return cases


def load_answer_keys(path: Path = DEFAULT_ANSWERS) -> dict[str, AnswerKey]:
    answers = _validate_rows(path, read_jsonl(path), AnswerKey)
    _reject_duplicate_ids(answers, "case_id")
    return {answer.case_id: answer for answer in answers}


def validate_dataset_alignment(cases: list[ScenarioCase], answer_keys: dict[str, AnswerKey]) -> None:
    case_ids = {case.case_id for case in cases}
    answer_ids = set(answer_keys)
    missing_answers = sorted(case_ids - answer_ids)
    orphan_answers = sorted(answer_ids - case_ids)
    if missing_answers:
        raise ValueError(f"missing answer keys for cases: {', '.join(missing_answers)}")
    if orphan_answers:
        raise ValueError(f"orphan answer keys without scenarios: {', '.join(orphan_answers)}")


def load_frameworks(path: Path = DEFAULT_REASONING_STRATEGIES) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    required = {"frameworks", "governance_modes", "response_contract"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"{path}: missing sections: {', '.join(sorted(missing))}")
    return data


def load_policies(
    path: Path = DEFAULT_STAGE_POLICIES,
    frameworks: dict[str, Any] | None = None,
) -> dict[str, StagePolicy]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    rows = data.get("policies", data)
    policies = _validate_rows(path, rows, StagePolicy)
    _reject_duplicate_ids(policies, "policy_id")

    if frameworks is not None:
        adapters = frameworks.get("stage_arms", {})
        chosen_arms = {
            arm
            for policy in policies
            for arm in policy.stage_assignments.values()
        }
        missing_adapters = sorted(chosen_arms - set(adapters))
        if missing_adapters:
            raise ValueError(f"missing stage arm adapters: {', '.join(missing_adapters)}")

    return {policy.policy_id: policy for policy in policies}


def load_tool_catalog(path: Path = DEFAULT_TOOL_CATALOG) -> ToolCatalog:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    rows = data.get("tools", data)
    definitions = [ToolDefinition.model_validate(row) for row in rows]
    return ToolCatalog(definitions={definition.name: definition for definition in definitions})
