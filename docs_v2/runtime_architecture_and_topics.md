# Runtime mimarisi, launch profilleri ve topic sözleşmeleri

> Kaynak sınırı: Bu sayfa aktif `teknofest_iha/nodes/*`, `teknofest_iha/interfaces/*`, `launch/*.launch.py` ve `config/*.yaml` okunarak genişletildi. `docs/` bağlamdır; otorite değildir. `build/`, `install/`, `log/` çıktıları stale olabilir.

## Node graph

- **[Kodla doğrulandı]** `perception_node`: `sensor_msgs/Image` kamera alır, OpenCV sonucu `/perception/raw_detections` JSON ve opsiyonel `/perception/debug_image` yayınlar.
- **[Kodla doğrulandı]** `fusion_node`: `/perception/raw_detections` tüketir, `/fusion/target` ve `/fusion/status` yayınlar.
- **[Kodla doğrulandı]** `mission_manager_node`: `/fusion/target`, `/drone/state`, `/drone/local_position`, `/drone/altitude`, `/drone/global_origin`, `/safety/status`, `/mission/cmd_start` tüketir; `/drone/cmd_mode`, `/drone/cmd_arm`, `/drone/cmd_takeoff`, `/drone/cmd_velocity`, `/drone/cmd_land`, `/drone/cmd_drop`, `/mission/state`, `/mission/event` yayınlar.
- **[Kodla doğrulandı]** `mavlink_bridge_node`: `/drone/cmd_*` tüketir, `/drone/state`, `/drone/local_position`, `/drone/altitude`, `/drone/global_position`, `/drone/gps_status`, `/drone/global_origin`, `/drone/home_position`, `/drone/status` yayınlar. Ek gizli/az dokümante tüketici: `/drone/cmd_position`.
- **[Kodla doğrulandı]** `safety_monitor_node`: `/drone/local_position` tüketir, `/safety/status` yayınlar.

Runtime topic’lerinin çoğu gerçek ROS custom message değil, `std_msgs/msg/String` içinde JSON taşır. Görüntü tarafında `sensor_msgs/msg/Image` kullanılır. JSON şemaları dataclass ve helper fonksiyonlarla kısmen merkezileşmiştir (`teknofest_iha/interfaces/detection_models.py`, `teknofest_iha/interfaces/drone_models.py`), fakat schema registry/ROS IDL yoktur.

## Major topic publisher -> consumer zincirleri

| Topic | Tip | Publisher | Consumer | Sözleşme / not |
|---|---|---|---|---|
| `/camera/raw` | `sensor_msgs/Image` | `ros_gz_bridge` remap (`launch/full_sim.launch.py`, `camera_bridge.launch.py`) veya saha kamera bridge’i **[Repo’dan çıkarılamaz]** | `perception_node` (`camera_topic`, YAML) ve `camera_frame_repeater_node` | Karar/algı stream’i. `config/perception.yaml` default’u budur. |
| `/camera` | `sensor_msgs/Image` | `camera_frame_repeater_node` | Display/recording/debug tüketicileri olabilir; `perception_node` ancak param override yoksa node default olarak `/camera` dinler | Launch yorumuna göre tekrar edilen görüntü; `/camera/raw` ile karıştırılmamalı. |
| `/perception/raw_detections` | `std_msgs/String` JSON | `PerceptionNode.on_image()` | `FusionNode.on_raw()` | `RawDetectionPacket.to_json()`: `frame_id,timestamp,opencv`. |
| `/perception/status` | `std_msgs/String` JSON | `perception_node` | Konsol/debug tüketimi repo’dan kesin çıkarılamaz | Şu an OK JSON veya startup exception dışı sınırlı sinyal. |
| `/perception/debug_image` | `sensor_msgs/Image` | `perception_node` | Debug viewer/recorder bağlamı | `publish_debug_image` true ise BGR debug image yayınlanır. |
| `/fusion/target` | `std_msgs/String` JSON | `fusion_node` | `mission_manager_node`, console/recorder/debug bağlamı | Mission target durumu ve release gate bilgisi. |
| `/fusion/status` | `std_msgs/String` JSON | `fusion_node` | Gözlemsel; zorunlu mission consumer yok | OK/ERROR JSON. |
| `/drone/cmd_mode` | `std_msgs/String` JSON | `mission_manager_node` | `mavlink_bridge_node.on_mode()` | `{command:"set_mode", mode:"GUIDED|RTL|...", timestamp}`. |
| `/drone/cmd_arm` | `std_msgs/String` JSON | `mission_manager_node` | `mavlink_bridge_node.on_arm()` | `{command:"arm", arm:true|false, timestamp}`; köprü ACK parse etmez. |
| `/drone/cmd_takeoff` | `std_msgs/String` JSON | `mission_manager_node` | `mavlink_bridge_node.on_takeoff()` | `{command:"takeoff", altitude_m:number, timestamp}`. |
| `/drone/cmd_velocity` | `std_msgs/String` JSON | `mission_manager_node` | `mavlink_bridge_node.on_velocity()` | Local NED velocity’ye çevrilmiş `vx,vy,vz,yaw_rate?`. SEARCH dışında mission geofence clamp yok. |
| `/drone/cmd_position` | `std_msgs/String` JSON | **Mission producer yok**; harici node/script olabilir **[Repo’dan çıkarılamaz]** | `mavlink_bridge_node.on_position()` | `{x,y,z,yaw?}` consumer vardır, mission manager yayınlamaz. |
| `/drone/cmd_land` | `std_msgs/String` JSON | `mission_manager_node` | `mavlink_bridge_node.on_land()` | LAND/failsafe_land command string’i köprüde ayırt edilmez; land çağrılır. |
| `/drone/cmd_drop` | `std_msgs/String` JSON | `mission_manager_node` | `mavlink_bridge_node.on_drop()` | Dry-run true ise köprü servo göndermez, `DROP_DRY_RUN` status yayınlar. |
| `/drone/state` | `std_msgs/String` JSON | `mavlink_bridge_node` | `mission_manager_node` | `DroneState`: connected/armed/mode/system/component/heartbeat. |
| `/drone/local_position` | `std_msgs/String` JSON | `mavlink_bridge_node` | `mission_manager_node`, `safety_monitor_node` | `LocalPosition`: NED x/y/z/vx/vy/vz. |
| `/drone/altitude` | `std_msgs/String` JSON | `mavlink_bridge_node` | `mission_manager_node` | `Altitude`: relative/AMSL. Mission local z negatifse onu öncelikli kullanır. |
| `/drone/global_position` | `std_msgs/String` JSON | `mavlink_bridge_node` | Henüz mission consumer yok | `GlobalPosition`: `lat_deg,lon_deg,relative_m,amsl_m,timestamp`; `GLOBAL_POSITION_INT` parse-if-arrives. |
| `/drone/gps_status` | `std_msgs/String` JSON | `mavlink_bridge_node` | Henüz mission consumer yok | `GpsStatus`: `fix_type,satellites_visible,eph,epv,hdop,timestamp`; `eph/epv` raw MAVLink numeric, `hdop=null`. |
| `/drone/global_origin` | `std_msgs/String` JSON | `mavlink_bridge_node` | `mission_manager_node` | `GlobalOrigin`: `lat_deg,lon_deg,alt_m,timestamp`; `GPS_GLOBAL_ORIGIN` parse-if-arrives. `mission_field_path` configured ise field WGS84->LOCAL_NED geometry için precondition’dır. |
| `/drone/home_position` | `std_msgs/String` JSON | `mavlink_bridge_node` | Henüz mission consumer yok | `HomePosition`: `lat_deg,lon_deg,alt_m,x,y,z,timestamp`; `HOME_POSITION` parse-if-arrives. |
| `/drone/status` | `std_msgs/String` JSON | `mavlink_bridge_node` | Gözlemsel/console bağlamı | CONNECTED/OK/ERROR/DROP_DRY_RUN; ACK health kapsamı sınırlı. |
| `/safety/status` | `std_msgs/String` JSON | `safety_monitor_node` | `mission_manager_node` | Rich JSON yayınlanır; mission sadece `status` alanını okur. |
| `/mission/state` | `std_msgs/String` JSON | `mission_manager_node` | Console/recorder/debug bağlamı | State, active target, search status, nav/local konum. Field configured ama hazır değilse `FIELD_NOT_READY` + `field_ready:false` + `field_error`. |
| `/mission/event` | `std_msgs/String` JSON | `mission_manager_node` | Recorder/console bağlamı | Drop event’i `/drone/cmd_drop` ile aynı payload olabilir. |
| `/mission/cmd_start` | `std_msgs/String` | Harici operator/console **[Repo’dan çıkarılamaz]** | `mission_manager_node.on_start_command()` | `start,true,1,go` kabul edilir. Field autostart false iken gerekir. |

## Launch profilleri

| Launch | Başlatılan ana node/process | Config defaultları | Autostart sonucu | Caveat |
|---|---|---|---|---|
| `launch/field_mission.launch.py` | perception, fusion, mavlink_bridge, safety_monitor, mission_manager, mission_console | perception/fusion/mission + `mavlink_gcs_router.yaml` | Launch arg default `false`, mission param override edilir | Saha/GCS router profili; `/mission/cmd_start` gerekir. Field Setup Tool çıktısı için `mission_field_path:=/path/to/mission_field.json` verilebilir. |
| `launch/mission.launch.py` | mavlink_bridge, safety_monitor, mission_manager | `mission.yaml`, `mavlink.yaml` | Override yok; `MissionManagerNode` default `autostart=True` çünkü `mission.yaml` autostart içermez | Perception/fusion yoksa `WAIT_FOR_CAMERA` bekler. |
| `launch/perception.launch.py` | perception, fusion | `perception.yaml`, `fusion.yaml` | Mission yok | Algı-füzyon izolasyonu. |
| `launch/full_sim.launch.py` | camera bridge process, frame repeater, perception, fusion, mavlink, safety, mission | perception/fusion/mission + `mavlink.yaml` | Override yok; mission default true | Gazebo/SITL içeriği var; bu görevde çalıştırılmadı. |
| `launch/camera_bridge.launch.py` | `ros_gz_bridge` process, `camera_frame_repeater_node` | Inline paramlar | Mission yok | `/downward_camera/image` -> `/camera/raw`, repeater -> `/camera`. |

**/camera/raw vs /camera ayrımı:** Launch yorumları `camera_bridge.launch.py` ve `full_sim.launch.py` içinde `/camera/raw` için “decision stream”, `/camera` için “display/recording” der. `perception_node` kaynak default’u `/camera` olsa da paket config’i (`config/perception.yaml`) bunu `/camera/raw` yapar. Bu yüzden runtime değerlendirmede kullanılan launch+config birlikte okunmalıdır.

## JSON topic kontrat özeti

- `/perception/raw_detections`: `RawDetectionPacket(frame_id,timestamp,opencv[])` (`teknofest_iha/interfaces/detection_models.py`).
- `/fusion/target`: `FusedTargetPacket(frame_id,timestamp,primary_target,state,targets[],selected)`; fused target içinde `target_state`, `perception_validated`, `release_gate`, `drop_ready`, `lock_counter` gibi alanlar eklenir.
- `/drone/state`: `DroneState(connected,armed,mode,system_id,component_id,last_heartbeat_s,timestamp)`.
- `/drone/local_position`: `LocalPosition(x,y,z,vx,vy,vz,frame,timestamp)`; NED varsayılır.
- `/drone/altitude`: `Altitude(relative_m,amsl_m,timestamp)`.
- `/drone/global_position`: `GlobalPosition(lat_deg,lon_deg,relative_m,amsl_m,timestamp)`; converter/projection katmanı yoktur.
- `/drone/gps_status`: `GpsStatus(fix_type,satellites_visible,eph,epv,hdop,timestamp)`; `eph/epv` raw MAVLink numeric olarak taşınır, `hdop` güvenli eşleme olmadığı için `null`.
- `/drone/global_origin`: `GlobalOrigin(lat_deg,lon_deg,alt_m,timestamp)`.
- `/drone/home_position`: `HomePosition(lat_deg,lon_deg,alt_m,x,y,z,timestamp)`.
- `/safety/status`: rich JSON: `status,x,y,local_x,local_y,coordinate_frame,timestamp`.

## Komut şemaları

`command_json(command, **params)` tüm `/drone/cmd_*` komutlarına `command` ve `timestamp` ekler.

- `/drone/cmd_mode`: `{command:"set_mode", mode:"GUIDED|RTL|..."}`
- `/drone/cmd_arm`: `{command:"arm", arm:true|false}`
- `/drone/cmd_takeoff`: `{command:"takeoff", altitude_m:number}`
- `/drone/cmd_velocity`: `{command:"velocity", vx, vy, vz, yaw_rate?}`
- `/drone/cmd_position`: `{x,y,z,yaw?}` köprüde desteklenir; mission manager yayınlamaz.
- `/drone/cmd_land`: `{command:"land"}` veya failsafe land komutu.
- `/drone/cmd_drop`: `{command:"drop_payload", target_type,dry_run,servo,pwm,reset_pwm,hold_seconds,...}`

> ⚠️ Safety-critical: JSON/String kontratları ad-hoc validasyonludur; exhaustive serialization testi yoktur.
