import json
from pathlib import Path

import pytest

from dedutive.data import load_frameworks, load_policies


ROOT = Path(__file__).resolve().parents[1]


def test_load_policies_accepts_baseline_policy_file():
    frameworks = load_frameworks()
    policies = load_policies(ROOT / "data" / "strategies" / "stage_policies.json", frameworks)

    assert policies["baseline_a"].stage_assignments["framing"] == "grade"
    assert policies["generic_baseline"].stage_assignments["review"] == "generic"


def test_load_policies_rejects_duplicate_policy_id(tmp_path):
    path = tmp_path / "policies.json"
    path.write_text(
        json.dumps(
            {
                "policies": [
                    {
                        "policy_id": "dup",
                        "description": "One",
                        "stage_assignments": {
                            "framing": "grade",
                            "hypothesis": "kt",
                            "check_selection": "kt",
                            "decision": "fordec",
                            "review": "single_loop",
                        },
                    },
                    {
                        "policy_id": "dup",
                        "description": "Two",
                        "stage_assignments": {
                            "framing": "safe",
                            "hypothesis": "rpd",
                            "check_selection": "shor",
                            "decision": "care",
                            "review": "nits",
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate policy_id"):
        load_policies(path, load_frameworks())


def test_load_policies_rejects_arm_missing_adapter(tmp_path):
    path = tmp_path / "policies.json"
    path.write_text(
        json.dumps(
            {
                "policies": [
                    {
                        "policy_id": "missing_adapter",
                        "description": "Uses a valid arm with missing adapter.",
                        "stage_assignments": {
                            "framing": "grade",
                            "hypothesis": "kt",
                            "check_selection": "kt",
                            "decision": "care",
                            "review": "single_loop",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    frameworks = load_frameworks()
    frameworks["stage_arms"].pop("care")

    with pytest.raises(ValueError, match="missing stage arm adapters"):
        load_policies(path, frameworks)
