import json

import config
from control.state_machine import CANDIDATE, LOCKED, TRACKING, TargetStateMachine
from teknofest_iha.adapters.fusion_adapter import FusionAdapter
from teknofest_iha.interfaces.detection_models import FusedTargetPacket, RawDetectionPacket


LEGACY_DETECTOR_PREFIX = "yo" + "lo"


def _fused(confidence=0.9, mode="contour"):
    return {
        "target_type": "red_square",
        "error": (0.0, 0.0),
        "fusion_confidence": confidence,
        "detection_mode": mode,
        "observation_valid": mode == "contour",
        "shape_valid": mode == "contour",
    }


def _direct_cv(frame_id=1, confidence=0.95):
    return {
        "source": "opencv",
        "target_type": "red_square",
        "bbox": (10, 10, 20, 20),
        "center": (20, 20),
        "confidence": confidence,
        "state": "DETECTED",
        "frame_id": frame_id,
        "error": (0.0, 0.0),
        "detection_mode": "contour",
        "observation_valid": True,
        "shape_valid": True,
        "validation_reason": "ok",
    }


def _continuity_cv(mode, frame_id=1):
    source = "opencv_kalman" if mode == "kalman" else "opencv"
    state = "PREDICTED" if mode == "kalman" else "DETECTED"
    return {
        "source": source,
        "target_type": "red_square",
        "bbox": (10, 10, 20, 20),
        "center": (20, 20),
        "confidence": 0.95,
        "state": state,
        "frame_id": frame_id,
        "error": (0.0, 0.0),
        "detection_mode": mode,
        "observation_valid": False,
        "shape_valid": False,
        "validation_reason": f"{mode}_fallback",
    }


def test_one_frame_advances_state_machine_once():
    machine = TargetStateMachine()

    assert machine.update(_fused(), True, frame_id=10) == CANDIDATE
    assert machine.update(_fused(), True, frame_id=10) == CANDIDATE

    assert machine.cv_seen_counter == 1
    assert machine.lock_counter == 0


def test_candidate_warmup_precedes_lock():
    machine = TargetStateMachine()

    assert machine.update(_fused(), True, frame_id=1) == CANDIDATE
    assert machine.update(_fused(), True, frame_id=2) == CANDIDATE
    assert machine.update(_fused(), True, frame_id=3) == LOCKED


def test_single_direct_validated_observation_does_not_immediately_lock():
    adapter = FusionAdapter("red_square", [])
    packet = RawDetectionPacket(frame_id=1, timestamp=0.0, opencv=[_direct_cv(1)])

    selected = adapter.fuse_packet(packet).selected

    assert selected["perception_validated"] is True
    assert selected["target_state"] == CANDIDATE
    assert selected["fusion_confidence"] == selected["confidence"]


def test_direct_validated_observations_can_lock_without_external_verifier():
    adapter = FusionAdapter("red_square", [])

    states = []

    for frame_id in range(1, config.CANDIDATE_MIN_FRAMES + 3):
        packet = RawDetectionPacket(frame_id=frame_id, timestamp=0.0, opencv=[_direct_cv(frame_id)])
        states.append(adapter.fuse_packet(packet).selected["target_state"])

    assert states[-1] == LOCKED


def test_tracker_observation_does_not_advance_lock_or_lock():
    adapter = FusionAdapter("red_square", [])

    states = []

    for frame_id in range(1, config.CANDIDATE_MIN_FRAMES + 4):
        packet = RawDetectionPacket(frame_id=frame_id, timestamp=0.0, opencv=[_continuity_cv("tracker", frame_id)])
        states.append(adapter.fuse_packet(packet).selected["target_state"])

    machine = adapter.state_machine_by_target["red_square"]
    assert states[-1] == TRACKING
    assert machine.cv_seen_counter == 0
    assert machine.lock_counter == 0


def test_kalman_prediction_does_not_advance_lock_or_lock():
    adapter = FusionAdapter("red_square", [])
    states = []

    for frame_id in range(1, config.CANDIDATE_MIN_FRAMES + 4):
        packet = RawDetectionPacket(frame_id=frame_id, timestamp=0.0, opencv=[_continuity_cv("kalman", frame_id)])
        states.append(adapter.fuse_packet(packet).selected["target_state"])

    machine = adapter.state_machine_by_target["red_square"]
    assert states[-1] == TRACKING
    assert machine.cv_seen_counter == 0
    assert machine.lock_counter == 0


def test_lost_direct_observations_do_not_preserve_validation():
    adapter = FusionAdapter("red_square", [])
    for frame_id in range(1, config.CANDIDATE_MIN_FRAMES + 3):
        adapter.fuse_packet(RawDetectionPacket(frame_id=frame_id, timestamp=0.0, opencv=[_direct_cv(frame_id)]))
    assert adapter.state_machine_by_target["red_square"].state == LOCKED

    selected = adapter.fuse_packet(
        RawDetectionPacket(frame_id=20, timestamp=0.0, opencv=[_continuity_cv("tracker", 20)])
    ).selected

    machine = adapter.state_machine_by_target["red_square"]
    assert selected["perception_validated"] is False
    assert selected["target_state"] == TRACKING
    assert machine.lock_counter == 0


def test_fused_packet_preserves_validation_gate_fields():
    adapter = FusionAdapter("red_square", [])
    packet = RawDetectionPacket(frame_id=1, timestamp=0.0, opencv=[_direct_cv(1)])

    parsed = adapter.fuse_packet(packet)
    selected = FusedTargetPacket.from_json(parsed.to_json()).selected

    assert selected["detection_mode"] == "contour"
    assert selected["observation_valid"] is True
    assert selected["shape_valid"] is True
    assert selected["perception_validated"] is True
    assert "drop_perception_gate" in selected


def test_raw_packet_serializes_without_compatibility_verifier_fields():
    packet = RawDetectionPacket(frame_id=1, timestamp=0.0, opencv=[])
    data = json.loads(packet.to_json())

    assert data == {"frame_id": 1, "timestamp": 0.0, "opencv": []}


def test_raw_packet_parser_tolerates_old_extra_fields_without_reemitting_them():
    old_text = json.dumps(
        {
            "frame_id": 1,
            "timestamp": 0.0,
            "opencv": [],
            LEGACY_DETECTOR_PREFIX: [{"source": "old"}],
            f"{LEGACY_DETECTOR_PREFIX}_ran": True,
            f"{LEGACY_DETECTOR_PREFIX}_age_frames": 0,
        }
    )

    parsed = RawDetectionPacket.from_json(old_text)

    assert parsed.opencv == []
    assert LEGACY_DETECTOR_PREFIX not in json.loads(parsed.to_json())


def test_release_gate_does_not_advance_state_twice_in_one_packet():
    adapter = FusionAdapter("red_square", [])
    state_machine = adapter.state_machine_by_target["red_square"]
    state_machine.cv_seen_counter = config.CANDIDATE_MIN_FRAMES
    state_machine.lock_counter = config.LOCK_MIN_FRAMES - 1
    packet = RawDetectionPacket(frame_id=50, timestamp=0.0, opencv=[_direct_cv(50)])

    selected = adapter.fuse_packet(packet).selected

    assert selected["target_state"] == LOCKED
    assert selected["release_gate"] is True
    assert state_machine.lock_counter == config.LOCK_MIN_FRAMES


def test_fusion_output_has_no_verifier_named_fields():
    adapter = FusionAdapter("red_square", [])
    selected = adapter.fuse_packet(RawDetectionPacket(frame_id=1, timestamp=0.0, opencv=[_direct_cv(1)])).selected

    assert selected["perception_validated"] is True
    assert not [key for key in selected if LEGACY_DETECTOR_PREFIX in key.lower()]
