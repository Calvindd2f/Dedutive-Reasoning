"""Deprecated import path. Use dedutive.evaluation.scoring instead."""
from dedutive.evaluation.scoring import (  # noqa: F401
    FRAMEWORK_MARKERS,
    WEIGHTS,
    create_bandit_log_records,
    score_record,
    score_run_records,
)
