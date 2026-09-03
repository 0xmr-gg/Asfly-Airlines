"""Target-level fusion state machine.

This state machine answers only one question: how reliable is the current
target observation? It does not know about takeoff, RTL, servo channels, or
payload execution. Payload permission is expressed separately as release_gate.
"""

import config


SEARCH = "SEARCH"
CANDIDATE = "CANDIDATE"
TRACKING = "TRACKING"
UNSTABLE = "UNSTABLE"
LOCKED = "LOCKED"


class TargetStateMachine:
    def __init__(self):
        self.state = SEARCH
        self.cv_seen_counter = 0
        self.lock_counter = 0
        self.unstable_counter = 0
        self.last_frame_id = None
        self.payload_released = False

    def update(self, fused_target, has_opencv_target, frame_id=None):
        if frame_id is not None and frame_id == self.last_frame_id:
            return self.state
        self.last_frame_id = frame_id

        if not has_opencv_target or fused_target is None:
            self.cv_seen_counter = 0
            self.lock_counter = 0
            self.unstable_counter = 0
            self.state = SEARCH
            return self.state

        validated_observation = perception_validated(fused_target, has_opencv_target)
        fusion_conf = float(fused_target.get("fusion_confidence", 0.0))
        lock_condition = validated_observation and fusion_conf >= config.FUSION_CONF_THRESH

        if validated_observation:
            self.cv_seen_counter += 1
        else:
            self.cv_seen_counter = 0
            self.lock_counter = 0

        if not validated_observation:
            self.unstable_counter = 0
            self.state = TRACKING
        elif self.cv_seen_counter <= config.CANDIDATE_MIN_FRAMES:
            self.lock_counter = 0
            self.unstable_counter = 0
            self.state = CANDIDATE
        elif lock_condition:
            self.unstable_counter = 0
            self.lock_counter += 1
            self.state = LOCKED
        else:
            self.lock_counter = 0
            self.unstable_counter = 0
            self.state = TRACKING

        return self.state

    def mark_payload_released(self):
        self.payload_released = True


def perception_validated(fused_target, has_opencv_target=True):
    """Return True only for direct validated perception evidence.

    New OpenCV metadata marks contour detections as observation/shape valid and
    tracker/Kalman continuity as invalid. Older tests/packets may not include
    those fields; keep them compatible unless they explicitly identify a
    tracker/Kalman observation.
    """
    if fused_target is None or not has_opencv_target:
        return False
    if "perception_validated" in fused_target:
        return bool(fused_target.get("perception_validated"))
    mode = str(fused_target.get("detection_mode", ""))
    source = str(fused_target.get("source", ""))
    if mode in ("tracker", "kalman") or source == "opencv_kalman":
        return False
    if "observation_valid" in fused_target or "shape_valid" in fused_target:
        return bool(fused_target.get("observation_valid", False)) and bool(fused_target.get("shape_valid", False))
    return bool(has_opencv_target)
