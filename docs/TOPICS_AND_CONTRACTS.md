# ROS 2 Topic Contracts

Bu belge aktif runtime topic sozlesmelerini ozetler. Payload'lar custom ROS
message degil, `std_msgs/msg/String` icinde JSON'dur.

## Kamera

- `/camera/raw` (`sensor_msgs/msg/Image`): perception karar akisi.
- `/camera` (`sensor_msgs/msg/Image`): goruntuleme/kayit icin tekrar edilen akis.

## Perception

### `/perception/raw_detections`

Ureten: `perception_node`

Tuketen: `fusion_node`, observer/recorder node'lari

Aktif JSON ornegi:

```json
{
  "frame_id": 132,
  "timestamp": 1780000000.12,
  "opencv": [
    {
      "source": "opencv",
      "target_type": "red_square",
      "bbox": [220, 160, 44, 42],
      "center": [242, 181],
      "confidence": 0.91,
      "state": "DETECTED",
      "frame_id": 132,
      "error": [-78, -59],
      "detection_mode": "contour",
      "observation_valid": true,
      "shape_valid": true,
      "validation_reason": "ok"
    }
  ]
}
```

Direct contour/shape-valid observations are validation evidence. Tracker and
Kalman continuity observations may appear in the same list but are marked with
invalid validation metadata and do not provide lock/release validation.

## Fusion

### `/fusion/target`

Ureten: `fusion_node`

Tuketen: `mission_manager_node`, observer/recorder node'lari

Aktif JSON ornegi:

```json
{
  "frame_id": 132,
  "timestamp": 1780000000.24,
  "primary_target": "blue_square",
  "state": "LOCKED",
  "targets": [
    {
      "target_type": "red_square",
      "target_state": "LOCKED",
      "source": "fusion",
      "bbox": [220, 160, 44, 42],
      "center": [242, 181],
      "confidence": 0.91,
      "fusion_confidence": 0.91,
      "perception_validated": true,
      "lock_counter": 10,
      "unstable_counter": 0,
      "release_gate": true,
      "drop_ready": true,
      "drop_perception_gate": true
    }
  ],
  "selected": {
    "target_type": "red_square",
    "target_state": "LOCKED",
    "release_gate": true
  }
}
```

`release_gate` servo komutu degildir. Mission manager kendi center/lock/irtifa
kosullariyla birlikte degerlendirir.

## Mission, MAVLink ve safety

- `/mission/state`: mission state, active target, search/debug fields.
- `/mission/event`: payload/drop event JSON.
- `/drone/cmd_*`: mission manager'dan MAVLink bridge'e command JSON.
- `/drone/state`, `/drone/local_position`, `/drone/altitude`: MAVLink telemetry JSON.
- `/safety/status`: geofence status JSON.
