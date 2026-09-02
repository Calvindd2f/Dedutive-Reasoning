from dedutive.data import load_cases
from dedutive.decision.fordec import FordecStrategy
from dedutive.communication.nits import NitsStrategy
from dedutive.governance.vroom_yetton_jago import VroomYettonJagoStrategy
from dedutive.learning.single_loop import SingleLoopStrategy
from dedutive.orchestrator.session import TroubleshootingSession
from dedutive.orchestrator.trajectory import Trajectory
from dedutive.reasoning.kepner_tregoe import KepnerTregoeStrategy


def test_trajectory_records_ordered_steps():
    trajectory = Trajectory()
    trajectory.add_step("incident", {"surface_prompt": "trust relationship failed"})
    trajectory.add_step("framing", {"problem_frame": "single device auth failure"})

    steps = trajectory.as_list()

    assert steps[0]["stage"] == "incident"
    assert steps[1]["stage"] == "framing"
    assert steps[1]["content"]["problem_frame"] == "single device auth failure"


def test_troubleshooting_session_holds_scenario_and_strategies():
    scenario = load_cases()[0]
    session = TroubleshootingSession(
        scenario=scenario,
        reasoning=KepnerTregoeStrategy(),
        governance=VroomYettonJagoStrategy(),
        decision=FordecStrategy(),
        communication=NitsStrategy(),
        learning=SingleLoopStrategy(),
    )

    assert session.scenario.case_id == scenario.case_id
    assert session.reasoning.name == "Kepner-Tregoe"
    assert session.trajectory.as_list() == []
