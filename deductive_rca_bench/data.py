"""Deprecated import path. Use dedutive.data instead."""
from dedutive.data import (  # noqa: F401
    DEFAULT_ANSWERS,
    DEFAULT_SCENARIOS,
    DEFAULT_STAGE_POLICIES as DEFAULT_POLICIES,
    DEFAULT_REASONING_STRATEGIES as DEFAULT_FRAMEWORKS,
    DEFAULT_TOOL_CATALOG,
    load_answer_keys,
    load_cases,
    load_frameworks,
    load_policies,
    load_tool_catalog,
    read_jsonl,
    validate_dataset_alignment,
    write_jsonl,
)
