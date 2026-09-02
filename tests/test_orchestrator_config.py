from pathlib import Path


def test_load_experiment_config_from_yaml():
    from dedutive.orchestrator.config import load_experiment_config

    config = load_experiment_config(Path("configs/experiments/baseline_a.yaml"))

    assert config.reasoning == "kepner_tregoe"
    assert config.governance == "vroom_yetton"
    assert config.decision == "fordec"
    assert config.communication == "nits"
    assert config.learning == "single_loop"


def test_build_strategy_functions_dispatch_by_name():
    from dedutive.orchestrator.config import (
        build_communication_strategy,
        build_decision_strategy,
        build_governance_strategy,
        build_learning_strategy,
        build_reasoning_strategy,
    )

    assert build_reasoning_strategy("kepner_tregoe").name == "Kepner-Tregoe"
    assert build_reasoning_strategy("recognition_primed").name == "Recognition-Primed Decision"
    assert build_governance_strategy("vroom_yetton").name == "Vroom-Yetton-Jago"
    assert build_decision_strategy("fordec").name == "FORDEC"
    assert build_communication_strategy("nits").name == "NITS"
    assert build_learning_strategy("single_loop").loop_type == "single_loop"
    assert build_learning_strategy("double_loop").loop_type == "double_loop"


def test_experiment_config_builds_full_session(tmp_path):
    from dedutive.data import load_cases
    from dedutive.orchestrator.config import build_session_from_config, load_experiment_config

    config = load_experiment_config(Path("configs/experiments/baseline_b.yaml"))
    session = build_session_from_config(config, load_cases()[0])

    assert session.reasoning.name == "Recognition-Primed Decision"
    assert session.communication.name == "NITS"
