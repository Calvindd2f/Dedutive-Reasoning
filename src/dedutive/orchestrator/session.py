from __future__ import annotations

from dataclasses import dataclass, field

from dedutive.communication.protocol import CommunicationStrategy
from dedutive.decision.protocol import DecisionStrategy
from dedutive.governance.protocol import GovernanceStrategy
from dedutive.learning.protocol import LearningStrategy
from dedutive.models import ScenarioCase
from dedutive.orchestrator.trajectory import Trajectory
from dedutive.reasoning.protocol import ReasoningStrategy


@dataclass
class TroubleshootingSession:
    scenario: ScenarioCase
    reasoning: ReasoningStrategy
    governance: GovernanceStrategy
    decision: DecisionStrategy
    communication: CommunicationStrategy
    learning: LearningStrategy
    trajectory: Trajectory = field(default_factory=Trajectory)
