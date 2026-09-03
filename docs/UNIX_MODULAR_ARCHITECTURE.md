# Teknofest IHA Modular Architecture

Bu proje ROS 2 uzerinde Unix felsefesine yakin bir gorev mimarisi kurar:

- Her node tek bir isi yapar.
- Node'lar acik topic/JSON sozlesmeleri ile baglanir.
- Dis dunya bagimliliklari adapter katmaninda tutulur.
- Karar mantigi mumkun oldugunca saf Python siniflarinda kalir.

## Katmanlar

- `teknofest_iha/nodes/`: ROS 2 process wrapper'lari.
- `teknofest_iha/adapters/`: OpenCV, fusion ve MAVLink adapter sinirlari.
- `teknofest_iha/core/`: mission state, search, geofence, alignment ve payload yardimcilari.
- `teknofest_iha/interfaces/`: JSON payload veri modelleri.
- `vision/`: OpenCV detector, detection helpers, Kalman ve fusion helper'lari.
- `control/`: target-level state machine ve release-gate mantigi.

## Ana akis

```text
camera -> perception_node -> /perception/raw_detections -> fusion_node -> /fusion/target -> mission_manager_node -> /drone/cmd_* -> mavlink_bridge_node
```

Yan surecler:

```text
safety_monitor_node      -> /safety/status
mission_console_node     -> terminal state/status
mission_video_recorder   -> kayit videosu + overlay
camera_frame_repeater    -> display/recording stream'i
```

## Algilama ve fusion siniri

Perception sadece OpenCV renk/sekil hedef gozlemlerini uretir. Fusion bu
gozlemlerden hedef durumu ve algisal release gate hesaplar. Servo, arm, takeoff,
velocity, failsafe ve RTL karar/komutlari perception/fusion katmanina ait
degildir; mission manager ve MAVLink bridge tarafindadir.

`/perception/raw_detections` aktif sozlesmesi:

```json
{"frame_id": 1, "timestamp": 0.0, "opencv": []}
```

`/fusion/target` icindeki secili hedef; `target_state`,
`perception_validated`, `fusion_confidence`, `release_gate`, `drop_ready`,
`lock_counter` ve `unstable_counter` gibi alanlar tasir.

## Yarismaya hazirlik notu

Sim ve gercek IHA arasinda degismesi beklenenler kamera topic/kalibrasyon,
MAVLink port/baud, servo kanal/PWM, geofence sinirlari ve hedef/irtifa
parametreleridir. Ucus kontrol ve payload davranislari gercek arac olmadan
dogrulanmis sayilmamalidir.
