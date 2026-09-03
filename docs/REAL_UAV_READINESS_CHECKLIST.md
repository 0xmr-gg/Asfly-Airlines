# Real UAV Readiness Checklist

Bu belge simden veya masaustu gelistirmeden gercek IHA'ya geciste kontrol
edilecek maddeleri listeler. Donanim davranisi gercek arac uzerinde ayri
dogrulanmadan dogrulanmis sayilmaz.

## Degismemesi Beklenen Domain Kodlari

- `teknofest_iha/core/state_machine.py`
- `teknofest_iha/core/search_pattern.py`
- `teknofest_iha/core/alignment_controller.py`
- `teknofest_iha/core/geofence.py`
- `teknofest_iha/adapters/fusion_adapter.py`
- `vision/fusion.py`
- `control/state_machine.py`
- `control/payload_logic.py`

Sahada sorun cikarsa once parametre/topic/adapter katmani kontrol edilmelidir.

## Degismesi Muhtemel Parametreler

### Kamera / Perception

Dosya: `config/perception.yaml`

Kontroller:

- `camera_topic`
- `detect_targets`
- `publish_debug_image`

Gercek kamera icin once topic/FPS/encoding dogrulanir:

```bash
ros2 topic list
ros2 topic info /camera
ros2 topic hz /camera
```

### MAVLink

Dosya: `config/mavlink.yaml`

Kontroller:

- connection string / baudrate
- system/component id
- heartbeat
- mode/arming precondition'lari

Gercek Pixhawk'ta once sadece heartbeat test edilir; arm/takeoff komutu verilmez.

### Mission / Payload / Geofence

Dosya: `config/mission.yaml`

Kontroller:

- `takeoff_altitude_m`, `drop_altitude_m`
- `search_speed_mps`, `align_max_speed_mps`
- `center_tolerance_px`
- `payload_dry_run`, `payload_servo`, `payload_pwm`, `payload_reset_pwm`
- `coordinate_frame`, `target_specs_json`
- geofence `x_min/x_max/y_min/y_max`, warning/hard margin

## Servo / Payload Dogrulama

1. Servo kanali Mission Planner ile tek tek test edilir.
2. PWM ac/kapa degerleri not edilir.
3. `payload_dry_run=true` ile yazilim akisi izlenir.
4. Pervaneler sokuluyken `payload_dry_run=false` servo testi yapilir.
5. Ucus testinden once mekanik takilma kontrol edilir.

## Aşamali Gercek IHA Test Plani

1. Yazilim-only: ROS node'lar, kamera, `/perception/raw_detections`,
   `/fusion/target`; MAVLink baglanmaz.
2. MAVLink heartbeat: sadece `/drone/state` okunur; arm/takeoff yok.
3. Servo dry-run: `payload_dry_run=true`, terminal/event akisi izlenir.
4. Servo ground: pervaneler sokulu, sadece payload komutu denenir.
5. Tethered/dusuk irtifa: manual override hazir, kisa arama sahasi.
6. Tam rehearsal: OBS kaydi, mission console, kamera overlay, GCS telemetry.

## OBS Kaydi Icin Kanit Satirlari

```text
[MISSION] state=SEARCH_TARGET  geofence=OK
[VISION ] opencv=DETECTED  validation=VALIDATED
[FUSION ] target=blue_square  state=LOCKED
[GATE   ] release_gate=TRUE  lock_counter=10/10
[PAYLOAD] released=1/2
[MISSION] state=MISSION_COMPLETE
```

## Riskler

- Kamera gecikmesi veya frame drop: topic hz/encoding ve debug image izlenmeli.
- Coordinate frame tersligi: `coordinate_frame`, `nav_x/nav_y` ve GCS konumu
  karsilastirilmali.
- Payload servo yanlis kanal: Mission Planner servo output test ve PWM config.
- Geofence yanlis saha: saha koordinati yeniden olculmeli.
