from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TRAJECTORY_STAGES = (
    "incident",
    "framing",
    "hypothesis_generation",
    "evidence_selection",
    "evidence_observation",
    "hypothesis_update",
    "decision",
    "action",
    "verification",
    "learning",
    "communication",
)


@dataclass
class TrajectoryStep:
    stage: str
    content: dict[str, Any]


@dataclass
class Trajectory:
    steps: list[TrajectoryStep] = field(default_factory=list)

    def add_step(self, stage: str, content: dict[str, Any]) -> None:
        if stage not in TRAJECTORY_STAGES:
            raise ValueError(f"unknown trajectory stage: {stage}")
        self.steps.append(TrajectoryStep(stage=stage, content=content))

    def as_list(self) -> list[dict[str, Any]]:
        return [{"stage": step.stage, "content": step.content} for step in self.steps]
