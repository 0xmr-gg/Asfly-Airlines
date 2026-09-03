from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "teknofest_iha" / "nodes" / "perception_node.py"


def test_perception_node_has_no_model_or_compat_runtime_calls():
    text = SOURCE.read_text(encoding="utf-8")

    assert ".start()" not in text
    assert ".submit(" not in text
    assert ".poll_latest(" not in text
    assert ".stop()" not in text
    assert ("yo" + "lo") not in text.lower()
    assert "model_path" not in text
    assert "get_parameter(\"model_path\")" not in text


def test_perception_node_publishes_opencv_only_raw_packet():
    text = SOURCE.read_text(encoding="utf-8")

    assert "RawDetectionPacket(" in text
    assert "opencv=opencv_dets," in text
