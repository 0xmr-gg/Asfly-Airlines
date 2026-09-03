# Config ve test referansı

> Kaynak sınırı: aktif `config/*.yaml`, top-level `config.py`, node `declare_parameter/get_parameter` kullanımları ve `tests/test_*.py` dosya adları incelendi. Build/install kopyaları kaynak kabul edilmedi.

## Config envanteri

- `config/perception.yaml`: kamera/raw/debug/status topicleri, `primary_target`, `detect_targets`, `publish_debug_image`.
- `config/fusion.yaml`: raw/target/status topic, primary/secondary target.
- `config/mission.yaml`: mission ve safety node paramları. `end_action: rtl` declare edilir ama aktif final davranış state machine’de RTL’dir; param tüketilmez.
- `config/mavlink*.yaml`: bağlantı/timeout/source/auto_connect tüketilir. `mode` declare edilir ama startup default davranış olarak kullanılmaz.
- `config.py`: OpenCV HSV/shape filtreleri, tracker/Kalman süreklilik sınırları, fusion threshold ve release gate toleransları.

## Önemli anahtar ayrımları

- `CENTER_TOL_X/Y` (`config.py`) fusion `release_gate` ve console gibi alanlarda; `mission.yaml center_tolerance_px` mission centered kontrolünde kullanılır. Aynı değer olmak zorunda değildir.
- `target_specs_json` yalnız payload drop estimate için kullanılır; hedef sırasını veya gerçek saha koordinatını tek başına garanti etmez.
- `payload_dry_run=true` default: bridge servo göndermez ama mission payload released sayar.

## Test kapsamı

Mevcut test dosyaları saf/core davranışlara odaklıdır:

| Test | Kapsadığı alan | Açık gap |
|---|---|---|
| `tests/test_fusion_state_machine.py` | Target state/fusion lock davranışı ve raw/fused JSON alanları | Gerçek kamera/ROS node yok. |
| `tests/test_perception_opencv_only_source.py` | Perception source içinde model/compat alan kalmaması | AST/source düzeyi; ROS runtime değil. |
| `tests/test_opencv_detection_modes.py` | OpenCV contour/tracker/Kalman validation mode sözleşmesi | Gerçek kamera çeşitliliği yok. |
| `tests/test_state_machine.py` | Saf mission state transition | ROS topic wiring/MAVLink yok. |
| `tests/test_target_selection.py` | Visible unreleased scoring/promotion helper | Runtime timer race yok. |
| `tests/test_search_pattern.py` | Lawnmower waypoint/velocity | Gerçek flight dynamics yok. |
| `tests/test_geofence.py` | Rectangle geofence check/clamp | FC geofence upload yok. |
| `tests/test_coordinate_frame.py` | identity/gazebo_xy_swapped mapper | GPS/projection/yaw rotation yok. |
| `tests/test_alignment_controller.py` | Centering velocity math | Kamera distortion/latency yok. |
| `tests/test_payload_metrics.py` | Drop estimate math | Gerçek payload ballistics yok. |

## Kapsam dışı / boşluklar

- ROS node wiring ve launch/config integration test yok.
- MAVLink adapter gerçek/sim bağlantı testi yok.
- OpenCV image processing ve CSRT availability kapsamlı test değil.
- JSON serialization exhaustive contract testi sınırlıdır.
- Scripts saha davranışı test değil.

## Güvenli doğrulama yöntemleri

- Kaynak dosya okuma, unit testler ve statik import/grep kontrolleri güvenlidir.
- Gazebo/SITL bu görevde çalıştırılmadı; kabul kriteri olarak kullanılmamalı.
- Gerçek uçuş, servo ve Pixhawk davranışı ancak ayrı donanım test prosedürüyle doğrulanabilir.
