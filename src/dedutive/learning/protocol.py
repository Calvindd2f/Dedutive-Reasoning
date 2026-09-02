from __future__ import annotations

from typing import Protocol

from dedutive.models import LearningMode


class LearningStrategy(Protocol):
    name: str
    loop_type: LearningMode

    def adapter_text(self) -> str:
        ...
