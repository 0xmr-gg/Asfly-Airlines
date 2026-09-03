import pytest

pytest.importorskip("rclpy")
pytest.importorskip("std_msgs")

from teknofest_iha.nodes.mission_manager_node import MissionManagerNode


def _node_for_lock_check():
    node = MissionManagerNode.__new__(MissionManagerNode)
    node.lock_started_at = None
    node.lock_target = None
    node.lock_seconds = 0.0
    node.lock_min_confidence = 0.6
    return node


def test_mission_tracking_target_is_not_locked_for_drop():
    node = _node_for_lock_check()
    target = {
        "target_type": "red_square",
        "target_state": "TRACKING",
        "fusion_confidence": 0.95,
    }

    assert node._target_locked(target, centered=True) is False


def test_mission_locked_target_can_satisfy_lock_path():
    node = _node_for_lock_check()
    target = {
        "target_type": "red_square",
        "target_state": "LOCKED",
        "fusion_confidence": 0.95,
    }

    assert node._target_locked(target, centered=True) is True
