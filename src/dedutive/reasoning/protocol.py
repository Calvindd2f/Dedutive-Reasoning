from __future__ import annotations

from typing import Protocol

from dedutive.models import StageArm, StageName


class ReasoningStrategy(Protocol):
    name: str

    def stage_arms(self) -> dict[StageName, StageArm]:
        ...
