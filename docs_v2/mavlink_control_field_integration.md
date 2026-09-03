# MAVLink kontrol ve saha entegrasyonu

> Kaynak sınırı: `teknofest_iha/nodes/mavlink_bridge_node.py`, `teknofest_iha/adapters/mavlink_adapter.py`, `teknofest_iha/interfaces/drone_models.py`, `config/mavlink*.yaml`, `launch/{field_mission,mission}.launch.py` incelendi. Pixhawk, mode availability, arming precheck, servo ve FC geofence donanımda doğrulanmadı.

## Köprü ve adapter davranışı

- **[Kodla doğrulandı]** `mavlink_bridge_node.py` ROS JSON komutlarını `MavlinkAdapter` çağrılarına çevirir; mission sequencing içermez.
- **[Kodla doğrulandı]** `config/mavlink.yaml` ve `mavlink_gcs_router.yaml`: `connection=udpin:127.0.0.1:14551`, `auto_connect=true`, `heartbeat_timeout_s=30`, `telemetry_rate_hz=20`, `command_timeout_s=5`, `source_system=255`.
- **[Kodla doğrulandı]** Field profile `mavlink_gcs_router.yaml` MAVProxy/GCS router senaryosunu yorumlarda açıklar; `field_mission.launch.py` default olarak bunu kullanır.
- **[Kodla doğrulandı]** `mode` param declare edilir fakat startup/default mode olarak kullanılmaz; mode değişimi yalnız `/drone/cmd_mode` ile olur.

Launch/config/router ayrımı:

| Profil | MAVLink config | Default connection | Not |
|---|---|---|---|
| `launch/field_mission.launch.py` | `mavlink_gcs_router.yaml` | `udpin:127.0.0.1:14551` | Yorumlara göre MAVProxy fiziksel link’i tutar, ROS 14551, GCS 14550 alır. |
| `launch/mission.launch.py` | `mavlink.yaml` | `udpin:127.0.0.1:14551` | Aynı bağlantı string’i; router yorumu yok. |
| `launch/full_sim.launch.py` | `mavlink.yaml` | `udpin:127.0.0.1:14551` | Sim/Gazebo içeriği var; bu görevde çalıştırılmadı. |

Köprü paramları: `connection`, `heartbeat_timeout_s`, `telemetry_rate_hz`, `command_timeout_s`, `mode`, `source_system`, `auto_connect`. `auto_connect=true` ise node init sırasında `connect()` denenir; bağlantı hatası `/drone/status` ERROR yayınlar. `mode` startup set_mode değildir.

## ROS boundary: subscriptions/publishers

| Yön | Topic | Handler/publisher | Şema |
|---|---|---|---|
| Sub | `/drone/cmd_mode` | `on_mode()` | JSON `mode`; default fallback `GUIDED`. |
| Sub | `/drone/cmd_arm` | `on_arm()` | JSON `arm`; default true. |
| Sub | `/drone/cmd_takeoff` | `on_takeoff()` | JSON `altitude_m` zorunlu. |
| Sub | `/drone/cmd_velocity` | `on_velocity()` | JSON `vx/vy/vz`, `yaw_rate` default 0. |
| Sub | `/drone/cmd_position` | `on_position()` | JSON `x/y/z` zorunlu, `yaw` opsiyonel. Mission producer yok. |
| Sub | `/drone/cmd_land` | `on_land()` | Payload içeriği okunmaz; adapter `land()`. |
| Sub | `/drone/cmd_drop` | `on_drop()` | `dry_run` default true; false ise servo/pwm gerekir. |
| Pub | `/drone/state` | `state_pub` | `DroneState.to_json()`. |
| Pub | `/drone/local_position` | `local_pub` | `LocalPosition.to_json()`. |
| Pub | `/drone/altitude` | `altitude_pub` | `Altitude.to_json()`. |
| Pub | `/drone/status` | `status_pub` | CONNECTED/OK/ERROR/DROP_DRY_RUN JSON. |

## Telemetry parsing ve ACK limitleri

- **[Kodla doğrulandı]** Adapter heartbeat bekler, GCS heartbeat gönderir, data stream request eder.
- **[Kodla doğrulandı]** Parse edilen mesajlar: `HEARTBEAT`, `LOCAL_POSITION_NED`, `GLOBAL_POSITION_INT`.
- **[Kodla doğrulandı]** `COMMAND_ACK`, battery, GPS quality, EKF, FC failsafe parse edilmiyor. Heartbeat timeout sonrası sürekli health kapsamı sınırlı.
- **[Kodla doğrulandı]** Arm/takeoff/mode komutlarında dry-run yoktur; gerçek bridge bağlıysa komut gönderir. Mode/arm success sadece telemetry state’e bakılarak beklenir, ACK yoktur.

| MAVLink message | Kod | ROS alanı | Limit |
|---|---|---|---|
| `HEARTBEAT` | `_update_heartbeat()` | `DroneState.connected=True`, `armed`, `mode`, system/component, `last_heartbeat_s` | Heartbeat sonrası health/failsafe ayrıntısı parse edilmez. |
| `LOCAL_POSITION_NED` | `_handle_message()` | `LocalPosition(x,y,z,vx,vy,vz,frame="NED")` | Local origin ve frame hizası donanımda doğrulanmadı. |
| `GLOBAL_POSITION_INT` | `_handle_message()` | `Altitude(relative_m=relative_alt/1000, amsl_m=alt/1000)` | GPS kalite/fix sayısı parse edilmez. |
| `COMMAND_ACK` | Yok | Yok | Komut kabul/ret bilgisi gözden kaçabilir. |
| Battery/GPS/EKF/failsafe | Yok | Yok | `/drone/status` health kapsamı sınırlı. |

ACK/health caveat: `_call()` adapter metodu exception fırlatmazsa `/drone/status` `OK` yayınlar; bu, FC’nin komutu kabul ettiğini veya fiziksel aksiyonun gerçekleştiğini kanıtlamaz. `set_mode()` ve `arm()` bekleme döngüsünde telemetry state’i kontrol eder; `takeoff`, velocity, position, land fallback ve servo için explicit ACK parse yoktur.

## Komutlar

- `set_mode(mode)`: mode mapping ile `set_mode_send`; RTL mission tarafından `/drone/cmd_mode` `mode=RTL` olarak yapılır, `adapter.rtl()` doğrudan kullanılmaz.
- `arm/disarm`: ArduCopter arm/disarm.
- `takeoff`: `MAV_CMD_NAV_TAKEOFF` command_long.
- `send_velocity_ned` ve `send_position_ned`: `MAV_FRAME_LOCAL_NED`.
- `land`: önce LAND mode, hata olursa `MAV_CMD_NAV_LAND` fallback.
- `drop_payload`: `MAV_CMD_DO_SET_SERVO`, `hold_seconds` sleep, varsa reset PWM.

Command JSON ayrıntıları:

| ROS komutu | Bridge metodu | MAVLink adapter metodu | Zorunlu/opsiyonel alan |
|---|---|---|---|
| `/drone/cmd_mode` | `on_mode` | `set_mode(mode, command_timeout_s)` | `mode`; yoksa `GUIDED`. |
| `/drone/cmd_arm` | `on_arm` | `arm()` / `disarm()` | `arm`; yoksa true. |
| `/drone/cmd_takeoff` | `on_takeoff` | `takeoff(altitude_m)` | `altitude_m` zorunlu. |
| `/drone/cmd_velocity` | `on_velocity` | `send_velocity_ned(vx,vy,vz,yaw_rate)` | `vx/vy/vz` default 0; `yaw_rate` default 0. |
| `/drone/cmd_position` | `on_position` | `send_position_ned(x,y,z,yaw)` | `x/y/z` zorunlu; `yaw` opsiyonel. |
| `/drone/cmd_land` | `on_land` | `land()` | İçerik okunmaz. |
| `/drone/cmd_drop` | `on_drop` | Dry-run ise yok; değilse `drop_payload(servo,pwm,hold_seconds,reset_pwm)` | `dry_run` default true; false için `servo/pwm` gerekir. |

Servo dry-run davranışı köprü seviyesindedir: `on_drop()` `dry_run` true ise `MavlinkAdapter.drop_payload()` çağırmadan `/drone/status` `{"status":"DROP_DRY_RUN","target":...}` yayınlar. Mission manager bunu beklemez; kendi tarafında hedefi released sayıp state machine’i ilerletebilir.

> ⚠️ Safety-critical: servo channel/PWM, ArduPilot mode availability, arming prechecks, FC failsafe/geofence ve NED hizalaması donanımda doğrulanmadı.

## Field scripts caveat

**[Docs-only / bağlam]** Bazı script/dokümanlarda eski path veya GCS varsayımları bulunabilir. Runtime otoritesi launch/config/source üçlüsüdür. Gerçek saha entegrasyonunda `udpin:127.0.0.1:14551` router topolojisi, MAVProxy/GCS portları ve fiziksel Pixhawk bağlantısı ayrıca doğrulanmalıdır.
