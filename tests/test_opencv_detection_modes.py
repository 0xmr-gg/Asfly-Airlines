import json

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from teknofest_iha.interfaces.detection_models import RawDetectionPacket
from vision import opencv_detector
from vision.opencv_detector import OpenCVDetector


def _red_square_frame():
    frame = np.zeros((180, 180, 3), dtype=np.uint8)
    cv2.rectangle(frame, (50, 50), (130, 130), (0, 0, 255), -1)
    return frame


def test_direct_contour_detection_marks_observation_valid():
    detector = OpenCVDetector()

    _, detections = detector.detect(_red_square_frame(), frame_id=7)

    red = next(d for d in detections if d["target_type"] == "red_square")
    assert red["source"] == "opencv"
    assert red["state"] == "DETECTED"
    assert red["detection_mode"] == "contour"
    assert red["observation_valid"] is True
    assert red["shape_valid"] is True
    assert red["validation_reason"] == "ok"
    assert red["shape_score"] == red["confidence"]


def test_kalman_fallback_is_not_marked_observation_valid(monkeypatch):
    monkeypatch.setattr(opencv_detector, "create_csrt_tracker", lambda: None)
    detector = OpenCVDetector()

    detector.detect(_red_square_frame(), frame_id=1)
    _, detections = detector.detect(np.zeros((180, 180, 3), dtype=np.uint8), frame_id=2)

    red = next(d for d in detections if d["target_type"] == "red_square")
    assert red["source"] == "opencv_kalman"
    assert red["state"] == "PREDICTED"
    assert red["detection_mode"] == "kalman"
    assert red["observation_valid"] is False
    assert red["shape_valid"] is False
    assert red["validation_reason"] == "kalman_prediction"


def test_raw_detection_packet_preserves_added_detection_fields():
    det = {
        "source": "opencv",
        "target_type": "red_square",
        "bbox": (50, 50, 80, 80),
        "center": (90, 90),
        "confidence": 0.9,
        "state": "DETECTED",
        "frame_id": 3,
        "detection_mode": "contour",
        "observation_valid": True,
        "shape_valid": True,
        "validation_reason": "ok",
    }
    packet = RawDetectionPacket(frame_id=3, timestamp=0.0, opencv=[det])

    payload = json.loads(packet.to_json())

    assert payload["opencv"][0]["detection_mode"] == "contour"
    assert payload["opencv"][0]["observation_valid"] is True

    parsed = RawDetectionPacket.from_json(packet.to_json())

    assert parsed.opencv[0]["detection_mode"] == "contour"
    assert parsed.opencv[0]["observation_valid"] is True
    assert parsed.opencv[0]["shape_valid"] is True
    assert parsed.opencv[0]["validation_reason"] == "ok"
