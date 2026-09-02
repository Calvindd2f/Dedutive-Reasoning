from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, Field, field_validator

from dedutive.models import AnswerKey, Framework, ScenarioCase, ScriptedToolObservation


class DocumentedIssue(BaseModel):
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    task_family: str = Field(min_length=1)
    issue_summary: str = Field(min_length=1)
    symptoms: list[str] = Field(min_length=1)
    documented_root_cause: str = Field(min_length=1)
    documented_resolution: list[str] = Field(min_length=1)
    verification: list[str] = Field(min_length=1)
    unsafe_or_unnecessary: list[str] = Field(default_factory=list)
    tools_available: list[str] = Field(default_factory=lambda: ["envsense"])
    scripted_tool_observations: list[ScriptedToolObservation] = Field(default_factory=list)
    source_reference: str | None = None
    distractors: list[str] = Field(default_factory=list)
    task_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("documented_resolution", "verification", "symptoms")
    @classmethod
    def require_non_empty_items(cls, value: list[str]) -> list[str]:
        if not all(item.strip() for item in value):
            raise ValueError("items must be non-empty strings")
        return value


VARIANT_PROFILES: list[dict[str, Any]] = [
    {
        "suffix": "v01",
        "complexity": "moderate",
        "ambiguity_level": "medium",
        "blast_radius": "single_device",
        "time_pressure": "urgent",
        "change_recency": "recent_change",
        "access_constraints": ["remote_only"],
        "evidence_quality": "noisy",
        "risk_profile": "medium",
    },
    {
        "suffix": "v02",
        "complexity": "moderate",
        "ambiguity_level": "high",
        "blast_radius": "single_user",
        "time_pressure": "normal",
        "change_recency": "none",
        "access_constraints": ["local_admin_available"],
        "evidence_quality": "contradictory",
        "risk_profile": "medium",
    },
    {
        "suffix": "v03",
        "complexity": "high",
        "ambiguity_level": "medium",
        "blast_radius": "site",
        "time_pressure": "urgent",
        "change_recency": "recent_policy_change",
        "access_constraints": ["remote_only"],
        "evidence_quality": "noisy",
        "risk_profile": "high",
    },
    {
        "suffix": "v04",
        "complexity": "low",
        "ambiguity_level": "low",
        "blast_radius": "single_device",
        "time_pressure": "normal",
        "change_recency": "recent_restore",
        "access_constraints": ["cached_credentials_only", "local_admin_available"],
        "evidence_quality": "clean",
        "risk_profile": "low",
    },
]

DEFAULT_FRAMEWORKS: list[Framework] = ["kt", "fordec", "rpd"]


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    return cleaned.upper() or "ISSUE"


def load_documented_issues(path: Path) -> list[DocumentedIssue]:
    issues: list[DocumentedIssue] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            issue = DocumentedIssue.model_validate(row)
            if issue.source_id in seen:
                raise ValueError(f"duplicate source_id: {issue.source_id}")
            seen.add(issue.source_id)
            issues.append(issue)
    return issues


def _variant_prompt(issue: DocumentedIssue, profile: dict[str, Any]) -> str:
    symptom_text = " ".join(issue.symptoms)
    constraints = ", ".join(profile["access_constraints"])
    return (
        f"{issue.issue_summary} Symptoms: {symptom_text} "
        f"Operational context: evidence is {profile['evidence_quality']}, "
        f"time pressure is {profile['time_pressure']}, access constraints are {constraints}. "
        "Determine the likely cause, gather discriminating evidence, choose the least disruptive remediation, and verify the result."
    )


def _gold_evidence(issue: DocumentedIssue) -> list[str]:
    evidence = list(issue.symptoms[:2])
    evidence.append(issue.documented_root_cause)
    return evidence


def _gold_actions(issue: DocumentedIssue) -> list[str]:
    return list(issue.documented_resolution)


def _iter_variants(
    *,
    variants_per_source: int,
    frameworks: list[Framework],
    policies: list[str],
) -> Iterable[tuple[dict[str, Any], Framework, str | None]]:
    for index in range(variants_per_source):
        profile = VARIANT_PROFILES[index % len(VARIANT_PROFILES)]
        framework = frameworks[index % len(frameworks)]
        policy = policies[index % len(policies)] if policies else None
        yield profile, framework, policy


def generate_from_documented_issues(
    issues: list[DocumentedIssue],
    *,
    variants_per_source: int = 3,
    frameworks: list[Framework] | None = None,
    policies: list[str] | None = None,
) -> tuple[list[ScenarioCase], list[AnswerKey]]:
    selected_frameworks = frameworks or DEFAULT_FRAMEWORKS
    selected_policies = policies or []
    cases: list[ScenarioCase] = []
    answers: list[AnswerKey] = []

    for issue in issues:
        scenario_id = _slug(issue.source_id)
        for profile, framework, policy in _iter_variants(
            variants_per_source=variants_per_source,
            frameworks=selected_frameworks,
            policies=selected_policies,
        ):
            policy_part = f"-{policy}" if policy else ""
            case_id = f"{scenario_id}-{framework}{policy_part}-{profile['suffix']}"
            visible_facts = {
                "source_id": issue.source_id,
                "source_reference": issue.source_reference,
                "policy_variant": policy,
                "documented_issue_generated": True,
            }
            visible_facts.update(issue.task_metadata)
            distractors = issue.distractors or [
                "A nearby warning may be unrelated",
                "A user-reported recent change may be coincidental",
            ]
            case = ScenarioCase(
                case_id=case_id,
                scenario_id=scenario_id,
                title=issue.title,
                framework=framework,
                governance_mode="consultative" if profile["blast_radius"] in {"site", "tenant"} else "autonomous",
                briefing_mode="nits",
                learning_mode="double_loop" if profile["risk_profile"] == "high" else "single_loop",
                task_family=issue.task_family,
                complexity=profile["complexity"],
                ambiguity_level=profile["ambiguity_level"],
                blast_radius=profile["blast_radius"],
                time_pressure=profile["time_pressure"],
                change_recency=profile["change_recency"],
                access_constraints=profile["access_constraints"],
                evidence_quality=profile["evidence_quality"],
                risk_profile=profile["risk_profile"],
                tool_profile=issue.task_metadata.get("tool_profile", "generated"),
                surface_prompt=_variant_prompt(issue, profile),
                environment_facts_visible=visible_facts,
                tools_available=issue.tools_available,
                distractors=distractors,
                scripted_tool_observations=issue.scripted_tool_observations,
            )
            answer = AnswerKey(
                case_id=case_id,
                root_cause=issue.documented_root_cause,
                acceptable_remediations=issue.documented_resolution,
                gold_evidence=_gold_evidence(issue),
                gold_actions=_gold_actions(issue),
                unsafe_actions=issue.unsafe_or_unnecessary,
                verification_requirements=issue.verification,
                judge_notes={
                    "source_id": issue.source_id,
                    "source_reference": issue.source_reference,
                    "policy_variant": policy,
                    "generated_from_documented_issue": True,
                },
            )
            cases.append(case)
            answers.append(answer)

    return cases, answers
