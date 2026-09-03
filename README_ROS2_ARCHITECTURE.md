# Teknofest IHA ROS 2 Architecture

This package wraps the OpenCV-only perception/fusion pipeline and mission/MAVLink
code with ROS 2 nodes. Runtime topic payloads are JSON over `std_msgs/String`.

## Documentation Map

- `docs/UNIX_MODULAR_ARCHITECTURE.md`: process/module boundaries.
- `docs/TOPICS_AND_CONTRACTS.md`: runtime ROS topic contracts and JSON payloads.
- `docs/STATE_MACHINES.md`: target fusion and mission state machines.
- `docs/CODE_REFERENCE.md`: file-by-file operational code summary.
- `docs/REAL_UAV_READINESS_CHECKLIST.md`: real-aircraft integration checks.
- `docs/GCS_MAVLINK_INTEGRATION.md`: GCS/MAVLink routing notes.

## File/Class Plan

- `teknofest_iha/adapters/opencv_adapter.py`
  - `OpenCVAdapter`: calls `vision.opencv_detector.OpenCVDetector`.
- `teknofest_iha/adapters/fusion_adapter.py`
  - `FusionAdapter`: converts OpenCV detections into fused target packets with
    perception validation, target state, and release-gate fields.
- `teknofest_iha/adapters/mavlink_adapter.py`
  - `MavlinkAdapter`: ArduPilot/MAVLink transport and command details.
- `teknofest_iha/core/*`
  - Mission state machine, search pattern, geofence, alignment, payload helpers.
- `teknofest_iha/nodes/*`
  - ROS 2 node wrappers for perception, fusion, mission, safety, MAVLink,
    recording, console, and debug viewing.

## Main Topics

- `/camera/raw`: perception input `sensor_msgs/msg/Image`.
- `/perception/raw_detections`: JSON `frame_id`, `timestamp`, `opencv`.
- `/fusion/target`: fused target JSON with `perception_validated`,
  `target_state`, `release_gate`, `drop_ready`, counters, and selected target.
- `/drone/cmd_takeoff`, `/drone/cmd_velocity`, `/drone/cmd_land`,
  `/drone/cmd_drop`: JSON/String commands.
- `/drone/state`, `/drone/local_position`, `/drone/altitude`: telemetry/status.
- `/mission/state`, `/mission/event`: mission state and events.
