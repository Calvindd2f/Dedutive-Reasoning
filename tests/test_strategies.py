from dedutive.models import AssignmentContext


def _sample_context(**overrides):
    base = dict(
        issue_family="identity_auth",
        ambiguity="medium",
        blast_radius="single_device",
        time_pressure="urgent",
        evidence_quality="noisy",
        access_level="cached_only",
        recent_change=True,
        recurring_issue=False,
        user_impact="high",
    )
    base.update(overrides)
    return AssignmentContext(**base)


def test_kepner_tregoe_reasoning_strategy_stage_arms():
    from dedutive.reasoning.kepner_tregoe import KepnerTregoeStrategy

    strategy = KepnerTregoeStrategy()
    arms = strategy.stage_arms()

    assert strategy.name == "Kepner-Tregoe"
    assert arms["hypothesis"] == "kt"
    assert arms["check_selection"] == "kt"


def test_recognition_primed_reasoning_strategy_stage_arms():
    from dedutive.reasoning.recognition_primed import RecognitionPrimedStrategy

    strategy = RecognitionPrimedStrategy()
    arms = strategy.stage_arms()

    assert arms["hypothesis"] == "rpd"


def test_hybrid_reasoning_strategy_combines_two_strategies():
    from dedutive.reasoning.hybrid import HybridReasoningStrategy
    from dedutive.reasoning.kepner_tregoe import KepnerTregoeStrategy
    from dedutive.reasoning.recognition_primed import RecognitionPrimedStrategy

    strategy = HybridReasoningStrategy(
        primary=RecognitionPrimedStrategy(), secondary=KepnerTregoeStrategy()
    )
    arms = strategy.stage_arms()

    assert arms["hypothesis"] == "rpd"
    assert arms["check_selection"] == "kt"
    assert "Recognition-Primed Decision" in strategy.name
    assert "Kepner-Tregoe" in strategy.name


def test_vroom_yetton_jago_selects_mode_from_context():
    from dedutive.governance.vroom_yetton_jago import VroomYettonJagoStrategy

    strategy = VroomYettonJagoStrategy()

    narrow = strategy.select_mode(_sample_context(blast_radius="single_device"))
    broad = strategy.select_mode(_sample_context(blast_radius="site"))

    assert narrow == "autonomous"
    assert broad == "consultative"


def test_fordec_decision_strategy_adapter_text():
    from dedutive.decision.fordec import FordecStrategy

    strategy = FordecStrategy()

    assert strategy.name == "FORDEC"
    assert "Facts" in strategy.adapter_text()


def test_nits_communication_strategy_adapter_text():
    from dedutive.communication.nits import NitsStrategy

    strategy = NitsStrategy()

    assert strategy.name == "NITS"
    assert "Nature" in strategy.adapter_text()


def test_single_and_double_loop_learning_strategies():
    from dedutive.learning.single_loop import SingleLoopStrategy
    from dedutive.learning.double_loop import DoubleLoopStrategy

    single = SingleLoopStrategy()
    double = DoubleLoopStrategy()

    assert single.loop_type == "single_loop"
    assert double.loop_type == "double_loop"
    assert "immediate" in single.adapter_text().lower()
    assert "assumptions" in double.adapter_text().lower()
