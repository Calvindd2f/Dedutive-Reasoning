from __future__ import annotations

from typing import Protocol

from dedutive.models import AssignmentContext, GovernanceMode


class GovernanceStrategy(Protocol):
    name: str

    def select_mode(self, context: AssignmentContext) -> GovernanceMode:
        ...
