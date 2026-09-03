"""Geometry-level OpenCV fusion helpers."""

def pick_best_opencv_detection(detections):
    valid = [d for d in detections if d["source"] in ("opencv", "opencv_kalman")]
    if not valid:
        return None
    return max(valid, key=lambda d: (d["state"] == "DETECTED", d["confidence"]))


def fuse_detections(opencv_detections, frame_id):
    cv_det = pick_best_opencv_detection(opencv_detections)
    if cv_det is None:
        return None

    fused = dict(cv_det)
    fused.update(
        {
            "source": "fusion",
            "fusion_confidence": float(cv_det["confidence"]),
            "age_frames": int(frame_id - cv_det["frame_id"]),
        }
    )
    return fused
