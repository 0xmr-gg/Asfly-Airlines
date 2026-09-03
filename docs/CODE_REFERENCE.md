# Code Reference

Bu belge operasyonel kaynak dosyalarinin aktif runtime rolunu ozetler.

## ROS Nodes

- `teknofest_iha/nodes/perception_node.py`: kamera frame'i alir, OpenCV ile
  renk/sekil hedef gozlemleri uretir, `/perception/raw_detections`,
  `/perception/status` ve opsiyonel `/perception/debug_image` yayinlar.
- `teknofest_iha/nodes/fusion_node.py`: raw detection JSON'u alir,
  `FusionAdapter` ile hedef state/release alanlarini uretir, `/fusion/target`
  yayinlar.
- `teknofest_iha/nodes/mission_manager_node.py`: mission state machine'i,
  search/align/verify/drop/RTL kararlarini ve `/drone/cmd_*` komutlarini uretir.
- `teknofest_iha/nodes/mavlink_bridge_node.py`: mission komutlarini MAVLink'e,
  telemetry'yi ROS topic'lerine cevirir.
- `teknofest_iha/nodes/safety_monitor_node.py`: local position'dan geofence
  status JSON'u yayinlar.
- `mission_console_node`, `mission_video_recorder_node`, `debug_viewer_node`,
  `camera_frame_repeater_node`: gozlem, kayit ve display yardimci node'lari.

## Adapters

- `teknofest_iha/adapters/opencv_adapter.py`: `OpenCVDetector` ciktilarini
  enabled target listesine gore filtreler.
- `teknofest_iha/adapters/fusion_adapter.py`: hedef basina
  `TargetStateMachine` tutar; `perception_validated`, `target_state`,
  `fusion_confidence`, `release_gate`, `drop_ready`, `drop_perception_gate`,
  `lock_counter`, `unstable_counter` alanlarini uretir.
- `teknofest_iha/adapters/mavlink_adapter.py`: heartbeat, mode, arm/disarm,
  takeoff, velocity, land/RTL, servo payload ve telemetry transport adapter'idir.

## Core

- `teknofest_iha/core/state_machine.py`: mission state transition mantigi.
- `teknofest_iha/core/search_pattern.py`: lawnmower/serpentine arama rotasi.
- `teknofest_iha/core/alignment_controller.py`: goruntu merkez hatasini hiz
  komutuna cevirir.
- `teknofest_iha/core/geofence.py`: arama sahasi warning/violation ve clamp.
- `teknofest_iha/core/coordinate_frame.py`: local frame ile navigation frame
  arasinda donusum.
- `teknofest_iha/core/payload_controller.py`: payload birakilan hedef takibi.
- `teknofest_iha/core/payload_metrics.py`: drop estimate/raporlama yardimcisi.
- `teknofest_iha/core/target_selection.py`: gorunen ve unreleased hedef secimi.

## Interfaces

- `teknofest_iha/interfaces/detection_models.py`: `Detection`,
  `RawDetectionPacket`, `FusedTargetPacket` JSON modelleri.
- `teknofest_iha/interfaces/drone_models.py`: `DroneState`, `LocalPosition`,
  `Altitude` ve command JSON helpers.
- `teknofest_iha/interfaces/target_models.py`: hedef adlari/oncelik modeli.

## Vision ve Control

- `vision/opencv_detector.py`: HSV maskeleri, kontur bulma, karelik/solidity/alan
  filtreleri, tracker ve Kalman fallback metadata'si.
- `vision/fusion.py`: OpenCV detections icinden en uygun hedefi secip fusion
  dictionary'si uretir.
- `vision/detection_types.py`: bbox ve detection yardimci fonksiyonlari.
- `vision/kalman_filter.py`: OpenCV tarafindaki kisa sureli takip icin 2D Kalman.
- `vision/camera.py`: ROS ana akista dogrudan kullanilmayan legacy camera worker.
- `control/state_machine.py`: target-level SEARCH/CANDIDATE/TRACKING/UNSTABLE/LOCKED.
- `control/payload_logic.py`: release gate kosulunu hesaplar; servo komutu vermez.

## Scripts

- `scripts/prepare_obs_recording.sh`, `scripts/start_mission_for_obs.sh`,
  `scripts/start_teknofest_demo.sh`: demo/OBS yardimci baslaticilari.
- `scripts/stop_teknofest_stack.sh`: demo sureclerini durdurur.
- `scripts/randomize_teknofest_world.py`: hedef konumlarini kontrollu rastgelelestirir.
- `scripts/configure_sitl_params.py`: ArduPilot JSON backend parametre yardimcisi.
- `scripts/sitl_takeoff_smoke.py`: tam gorevden once takeoff saglik testi scripti.

## Legacy / Training

Eski egitim/model/dataset artifact'lari aktif runtime kontrati degildir. Bu
dokuman yalniz mevcut ROS/OpenCV-only mission source tree'i tarif eder.
