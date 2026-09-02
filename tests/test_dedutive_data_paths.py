from pathlib import Path


def test_default_paths_point_at_strategies_dir():
    from dedutive.data import DEFAULT_REASONING_STRATEGIES, DEFAULT_STAGE_POLICIES

    assert DEFAULT_REASONING_STRATEGIES == Path("data/strategies/reasoning.json").resolve()
    assert DEFAULT_STAGE_POLICIES == Path("data/strategies/stage_policies.json").resolve()


def test_load_cases_and_frameworks_from_new_locations():
    from dedutive.data import load_cases, load_frameworks, load_policies

    cases = load_cases()
    frameworks = load_frameworks()
    policies = load_policies(frameworks=frameworks)

    assert len(cases) == 30
    assert "kt" in frameworks["frameworks"]
    assert "baseline_a" in policies
