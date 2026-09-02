from __future__ import annotations

from dedutive.models import AssignmentContext, GovernanceMode


class VroomYettonJagoStrategy:
    name = "Vroom-Yetton-Jago"

    def select_mode(self, context: AssignmentContext) -> GovernanceMode:
        if context.blast_radius in {"site", "tenant", "multi_customer"}:
            return "consultative" if context.blast_radius == "site" else "group_decision"
        return "autonomous"
