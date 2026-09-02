from __future__ import annotations

from dedutive.models import StageArm, StageName


class RecognitionPrimedStrategy:
    name = "Recognition-Primed Decision"

    def stage_arms(self) -> dict[StageName, StageArm]:
        return {"framing": "safe", "hypothesis": "rpd", "check_selection": "shor"}
