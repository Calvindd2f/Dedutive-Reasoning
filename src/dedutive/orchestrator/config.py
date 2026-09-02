from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from dedutive.communication.nits import NitsStrategy
from dedutive.communication.protocol import CommunicationStrategy
from dedutive.decision.fordec import FordecStrategy
from dedutive.decision.protocol import DecisionStrategy
from dedutive.governance.protocol import GovernanceStrategy
from dedutive.governance.vroom_yetton_jago import VroomYettonJagoStrategy
from dedutive.learning.double_loop import DoubleLoopStrategy
from dedutive.learning.protocol import LearningStrategy
from dedutive.learning.single_loop import SingleLoopStrategy
from dedutive.models import ScenarioCase
from dedutive.orchestrator.session import TroubleshootingSession
from dedutive.reasoning.hybrid import HybridReasoningStrategy
from dedutive.reasoning.kepner_tregoe import KepnerTregoeStrategy
from dedutive.reasoning.protocol import ReasoningStrategy
from dedutive.reasoning.recognition_primed import RecognitionPrimedStrategy


@dataclass
class ExperimentConfig:
    reasoning: str
    governance: str
    decision: str
    communication: str
    learning: str


def load_experiment_config(path: Path) -> ExperimentConfig:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return ExperimentConfig(
        reasoning=data["reasoning"]["strategy"],
        governance=data["governance"]["strategy"],
        decision=data["decision"]["strategy"],
        communication=data["communication"]["strategy"],
        learning=data["learning"]["strategy"],
    )


def build_reasoning_strategy(name: str) -> ReasoningStrategy:
    if name == "kepner_tregoe":
        return KepnerTregoeStrategy()
    if name == "recognition_primed":
        return RecognitionPrimedStrategy()
    if name == "hybrid_kt_rpd":
        return HybridReasoningStrategy(primary=RecognitionPrimedStrategy(), secondary=KepnerTregoeStrategy())
    raise ValueError(f"unknown reasoning strategy: {name}")


def build_governance_strategy(name: str) -> GovernanceStrategy:
    if name == "vroom_yetton":
        return VroomYettonJagoStrategy()
    raise ValueError(f"unknown governance strategy: {name}")


def build_decision_strategy(name: str) -> DecisionStrategy:
    if name == "fordec":
        return FordecStrategy()
    raise ValueError(f"unknown decision strategy: {name}")


def build_communication_strategy(name: str) -> CommunicationStrategy:
    if name == "nits":
        return NitsStrategy()
    raise ValueError(f"unknown communication strategy: {name}")


def build_learning_strategy(name: str) -> LearningStrategy:
    if name == "single_loop":
        return SingleLoopStrategy()
    if name == "double_loop":
        return DoubleLoopStrategy()
    raise ValueError(f"unknown learning strategy: {name}")


def build_session_from_config(config: ExperimentConfig, scenario: ScenarioCase) -> TroubleshootingSession:
    return TroubleshootingSession(
        scenario=scenario,
        reasoning=build_reasoning_strategy(config.reasoning),
        governance=build_governance_strategy(config.governance),
        decision=build_decision_strategy(config.decision),
        communication=build_communication_strategy(config.communication),
        learning=build_learning_strategy(config.learning),
    )
