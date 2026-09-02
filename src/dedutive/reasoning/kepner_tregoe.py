from __future__ import annotations

from dedutive.models import StageArm, StageName


class KepnerTregoeStrategy:
    name = "Kepner-Tregoe"

    def stage_arms(self) -> dict[StageName, StageArm]:
        return {"framing": "grade", "hypothesis": "kt", "check_selection": "kt"}
