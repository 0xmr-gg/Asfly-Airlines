# ASFLY Mission Software Package

This repository currently contains the ROS 2 mission stack with OpenCV-only
perception, fusion, mission management, safety monitoring, MAVLink bridge, and
observer/recording nodes.

Current runtime perception path:

```text
camera image -> OpenCV color/shape detection -> raw detection JSON -> fusion target JSON -> mission manager
```

Runtime target validation is based on direct OpenCV contour/shape observations.
Tracker/Kalman continuity observations can keep visual tracking information, but
do not provide lock/release validation by themselves.

Training/model artifacts from older package layouts are not part of the active
runtime contract. See `README_ROS2_ARCHITECTURE.md` and `docs_v2/` for the
current architecture reference.
