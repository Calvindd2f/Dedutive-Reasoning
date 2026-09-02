from __future__ import annotations

from dedutive.models import StageArm, StageName
from dedutive.reasoning.protocol import ReasoningStrategy


class HybridReasoningStrategy:
    def __init__(self, *, primary: ReasoningStrategy, secondary: ReasoningStrategy) -> None:
        self.primary = primary
        self.secondary = secondary
        self.name = f"Hybrid({primary.name} + {secondary.name})"

    def stage_arms(self) -> dict[StageName, StageArm]:
        primary_arms = self.primary.stage_arms()
        secondary_arms = self.secondary.stage_arms()
        merged = dict(primary_arms)
        if "check_selection" in secondary_arms:
            merged["check_selection"] = secondary_arms["check_selection"]
        return merged
