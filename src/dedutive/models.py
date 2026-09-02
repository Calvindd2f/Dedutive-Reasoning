from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


Framework = Literal["kt", "fordec", "rpd"]
GovernanceMode = Literal["autonomous", "consultative", "group_decision"]
BriefingMode = Literal["nits"]
LearningMode = Literal["single_loop", "double_loop"]
Complexity = Literal["low", "moderate", "high"]
AmbiguityLevel = Literal["low", "medium", "high"]
BlastRadius = Literal["single_user", "single_device", "site", "tenant", "multi_customer"]
TimePressure = Literal["normal", "urgent", "sev1"]
ChangeRecency = Literal["none", "recent_change", "recent_restore", "recent_policy_change"]
EvidenceQuality = Literal["clean", "noisy", "contradictory"]
RiskProfile = Literal["low", "medium", "high"]
StageName = Literal["framing", "hypothesis", "check_selection", "decision", "review"]
StageArm = Literal[
    "safe",
    "grade",
    "3p",
    "generic",
    "kt",
    "rpd",
    "shor",
    "fordec",
    "care",
    "5d",
    "nits",
    "single_loop",
    "double_loop",
]

STAGE_ORDER: tuple[StageName, ...] = (
    "framing",
    "hypothesis",
    "check_selection",
    "decision",
    "review",
)

STAGE_CANDIDATE_ARMS: dict[StageName, list[StageArm]] = {
    "framing": ["safe", "grade", "3p", "generic"],
    "hypothesis": ["kt", "rpd", "shor", "generic"],
    "check_selection": ["kt", "shor", "generic"],
    "decision": ["fordec", "care", "5d", "generic"],
    "review": ["nits", "single_loop", "double_loop", "generic"],
}


class ScriptedToolObservation(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    observation: dict[str, Any] = Field(default_factory=dict)


class ScenarioCase(BaseModel):
    case_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    framework: Framework
    governance_mode: GovernanceMode
    briefing_mode: BriefingMode
    learning_mode: LearningMode
    task_family: str = Field(min_length=1)
    complexity: Complexity
    ambiguity_level: AmbiguityLevel
    blast_radius: BlastRadius
    time_pressure: TimePressure
    change_recency: ChangeRecency
    access_constraints: list[str] = Field(default_factory=list)
    evidence_quality: EvidenceQuality
    risk_profile: RiskProfile
    tool_profile: str = Field(min_length=1)
    surface_prompt: str = Field(min_length=1)
    environment_facts_visible: dict[str, Any] = Field(default_factory=dict)
    tools_available: list[str] = Field(default_factory=list)
    distractors: list[str] = Field(default_factory=list)
    scripted_tool_observations: list[ScriptedToolObservation] = Field(default_factory=list)

    @field_validator("case_id", "scenario_id")
    @classmethod
    def ids_must_not_contain_spaces(cls, value: str) -> str:
        if any(char.isspace() for char in value):
            raise ValueError("ids must not contain whitespace")
        return value


class AssignmentContext(BaseModel):
    issue_family: str
    ambiguity: str
    blast_radius: str
    time_pressure: str
    evidence_quality: str
    access_level: Literal["full", "limited", "remote_only", "cached_only"]
    recent_change: bool
    recurring_issue: bool
    user_impact: Literal["low", "medium", "high"]

    @classmethod
    def from_case(cls, case: ScenarioCase) -> "AssignmentContext":
        constraints = set(case.access_constraints)
        if "cached_credentials_only" in constraints:
            access_level = "cached_only"
        elif "remote_only" in constraints:
            access_level = "remote_only"
        elif "local_admin_available" in constraints:
            access_level = "full"
        else:
            access_level = "limited"

        recent_change = case.change_recency != "none"
        recurring_issue = bool(case.environment_facts_visible.get("recurring_issue", False))
        if case.time_pressure in {"urgent", "sev1"} or case.blast_radius in {"site", "tenant", "multi_customer"}:
            user_impact = "high"
        elif case.blast_radius in {"single_device", "single_user"}:
            user_impact = "medium"
        else:
            user_impact = "low"

        return cls(
            issue_family=case.task_family,
            ambiguity=case.ambiguity_level,
            blast_radius=case.blast_radius,
            time_pressure=case.time_pressure,
            evidence_quality=case.evidence_quality,
            access_level=access_level,
            recent_change=recent_change,
            recurring_issue=recurring_issue,
            user_impact=user_impact,
        )


class StageAssignment(BaseModel):
    stage: StageName
    chosen_arm: StageArm
    candidate_arms: list[StageArm]


class StagePolicy(BaseModel):
    policy_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    stage_assignments: dict[str, StageArm]

    @model_validator(mode="after")
    def validate_stage_assignments(self) -> "StagePolicy":
        stages = set(self.stage_assignments)
        expected = set(STAGE_ORDER)
        unknown = stages - expected
        missing = expected - stages
        if unknown:
            raise ValueError(f"unknown stages: {', '.join(sorted(unknown))}")
        if missing:
            raise ValueError(f"missing stages: {', '.join(sorted(missing))}")
        for stage, arm in self.stage_assignments.items():
            if arm not in STAGE_CANDIDATE_ARMS[stage]:
                raise ValueError(f"invalid arm for {stage}: {arm}")
        return self

    def assignments(self) -> list[StageAssignment]:
        return [
            StageAssignment(
                stage=stage,
                chosen_arm=self.stage_assignments[stage],
                candidate_arms=STAGE_CANDIDATE_ARMS[stage],
            )
            for stage in STAGE_ORDER
        ]


class StageReward(BaseModel):
    framing_quality: float = Field(ge=0.0, le=1.0)
    hypothesis_quality: float = Field(ge=0.0, le=1.0)
    check_selection_quality: float = Field(ge=0.0, le=1.0)
    decision_quality: float = Field(ge=0.0, le=1.0)
    verification_quality: float = Field(ge=0.0, le=1.0)
    risk_discipline: float = Field(ge=0.0, le=1.0)
    efficiency_penalty: float = Field(ge=0.0, le=1.0)
    hallucination_penalty: float = Field(ge=0.0, le=1.0)
    stage_reward: float = Field(ge=0.0, le=1.0)


class AnswerKey(BaseModel):
    case_id: str = Field(min_length=1)
    root_cause: str = Field(min_length=1)
    acceptable_remediations: list[str] = Field(min_length=1)
    gold_evidence: list[str] = Field(min_length=1)
    gold_actions: list[str] = Field(min_length=1)
    unsafe_actions: list[str] = Field(default_factory=list)
    verification_requirements: list[str] = Field(min_length=1)
    judge_notes: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required_args: list[str] = Field(default_factory=list)
    returns: list[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    tool: str = Field(min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)


class ToolObservation(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    observation: dict[str, Any] = Field(default_factory=dict)
    source: Literal["simulated", "error", "manual"] = "simulated"


class ToolInteraction(BaseModel):
    call: ToolCall
    observation: ToolObservation | None = None
    error: str | None = None


class Hypothesis(BaseModel):
    name: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    why_it_fits: list[str] = Field(default_factory=list)


class NextBestTest(BaseModel):
    test: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    expected_signal: str = Field(min_length=1)


class Decision(BaseModel):
    chosen_path: str = Field(min_length=1)
    why: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)


class NitsBrief(BaseModel):
    nature: str = Field(min_length=1)
    intention: str = Field(min_length=1)
    time: str = Field(min_length=1)
    special_instructions: str = Field(min_length=1)


class PostIncidentLearning(BaseModel):
    loop_type: LearningMode
    lesson: str = Field(min_length=1)


class ResponseContract(BaseModel):
    problem_frame: str = Field(min_length=1)
    known_facts: list[str] = Field(default_factory=list)
    key_unknowns: list[str] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(min_length=1)
    next_best_tests: list[NextBestTest] = Field(default_factory=list)
    decision: Decision
    execution_plan: list[str] = Field(min_length=1)
    verification_steps: list[str] = Field(default_factory=list)
    nits_brief: NitsBrief
    post_incident_learning: PostIncidentLearning
    stage_outputs: dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    case_id: str
    final_response: ResponseContract | dict[str, Any]
    tool_transcript: list[ToolInteraction] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreBreakdown(BaseModel):
    case_id: str
    total_score: int
    components: dict[str, int]
    penalties: list[str] = Field(default_factory=list)
    judge_artifact: dict[str, Any] = Field(default_factory=dict)
    policy_id: str | None = None
    output_summary: dict[str, Any] = Field(default_factory=dict)


class PolicyRunRecord(BaseModel):
    case_id: str
    scenario_id: str
    policy_id: str
    context: AssignmentContext
    stage: StageName
    chosen_arm: StageArm
    candidate_arms: list[StageArm]
    output_summary: dict[str, Any] = Field(default_factory=dict)
    stage_reward: StageReward
    final_score: int
