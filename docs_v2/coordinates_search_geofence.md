# Koordinatlar, arama ve geofence

> Kaynak sınırı: `teknofest_iha/core/{coordinate_frame,field_geometry,search_pattern,geofence}.py`, `teknofest_iha/nodes/{mission_manager_node,safety_monitor_node,mavlink_bridge_node}.py`, `config/mission.yaml` incelendi. FC/Mission Planner geofence yükleme davranışı donanımda doğrulanmadı; repoda buna ait kod bulunmadı.

## Coordinate frames

- **[Kodla doğrulandı]** `CoordinateFrameMapper` yalnız `identity` ve `gazebo_xy_swapped` davranışlarını destekler. Bilinmeyen mode identity gibi davranır.
- **[Kodla doğrulandı]** `config/mission.yaml` mission ve safety için `coordinate_frame: gazebo_xy_swapped` kullanır.
- **[Kodla doğrulandı]** MAVLink köprü `MAV_FRAME_LOCAL_NED` ile local NED hız/pozisyon gönderir.

| Mapper mode | `nav_xy_from_local(x,y)` | `local_velocity_from_nav(vx,vy)` | `nav_velocity_from_local(vx,vy)` | Kullanım |
|---|---|---|---|---|
| `identity` | `(x,y)` | `(vx,vy)` | `(vx,vy)` | Node defaultları ve bilinmeyen mode fallback. |
| `gazebo_xy_swapped` | `(local_y, local_x)` | `(nav_vy, nav_vx)` | `(local_vy, local_vx)` | `config/mission.yaml` mission+safety. |

Bu mapper yalnız XY değişimi yapar. Yaw rotasyonu, polygon-aware search dönüşümü veya NED/ENU genel dönüşümü değildir. MAVLink bridge global GPS/origin/home telemetry prerequisite topic’lerini (`/drone/global_position`, `/drone/gps_status`, `/drone/global_origin`, `/drone/home_position`) parse-if-arrives olarak yayınlar. `field_geometry.py` artık `mission_field.json` WGS84 köşelerini `/drone/global_origin` lat/lon’una göre küçük-alan equirectangular/local tangent yaklaşımıyla LOCAL_NED XY’ye projekte eder: x=north metre, y=east metre.

## `mission_field.json` ve field geometry

- **[Kodla doğrulandı]** Desteklenen kontrat sabittir: `version: 1`, `coordinate_system: "WGS84"`, tam 4 adet `{lat,lon}` köşe.
- **[Kodla doğrulandı]** `load_mission_field()` version/coordinate_system/köşe sayısı/lat-lon varlığı ve lat `[-90,90]`, lon `[-180,180]` aralığını doğrular; hata `FieldConfigError` üretir.
- **[Kodla doğrulandı]** `build_field_geometry()` sadece `/drone/global_origin` (`GlobalOrigin.lat_deg/lon_deg`) kullanır; `HOME_POSITION` kullanılmaz.
- **[Kodla doğrulandı]** Projeksiyon sonrası duplicate/near-duplicate köşe, self-intersection, concave/degenerate quadrilateral ve çok küçük alan hard fail olur. Köşe sırası centroid etrafında normalize edilir; bu yüzden kullanıcı cross-order geçse bile noktalar geçerli konveks dörtgen oluşturuyorsa kabul edilebilir.
- **[Kodla doğrulandı]** Field-local frame merkezi polygon centroid’idir. `u` ekseni en uzun edge yönü, `v` ekseni ona dik kısa yöndür; `ned_to_field_uv()` / `field_uv_to_ned()` roundtrip deterministiktir.
- **[Kodla doğrulandı]** `mission_field_path` boş değilse MissionManager dosyayı init sırasında doğrular ve geometry hazır olana kadar normal mission timer/state/action akışını çalıştırmaz; `/mission/state` içinde `FIELD_NOT_READY` yayınlar.
- **[Kodla doğrulandı]** `mission_field_path` boşsa legacy `search_x_min/x_max/y_min/y_max` rectangle davranışı korunur ve global origin gerekmez.
- Operatörler her koşu için `runtime/mission_field.json` dosyasını düzenleyip `mission_field_path:=runtime/mission_field.json` ile geçebilir. Repoya ekli dosya yalnız placeholder’dır; kullanımdan önce gerçek 4 WGS84 köşe ile değiştirilmelidir.

## Search area ve lawnmower

- **[Kodla doğrulandı]** `mission_field_path` boşsa search area eksene hizalı dikdörtgendir: `search_x_min/x_max/y_min/y_max`; config: `0..100`, `-12..12`.
- **[Kodla doğrulandı]** `LawnmowerSearchPattern` y_min’den y_max’e lane üretir, `lane_spacing_m` ile ilerler, x_min/x_max arasında alternating serpentine yapar. Field configured modda `FieldLawnmowerSearchPattern` aynı semantiği field-local `u/v` üzerinde `u_min/u_max/v_min/v_max` ile kullanır; lane’ler uzun eksen (`u`) boyunca gider ve hedef/hız LOCAL_NED XY’ye geri çevrilir.
- **[Kodla doğrulandı]** Nearest start yalnız ilk lane’in iki endpoint’ini karşılaştırır: `(x_max,y_min)` vs `(x_min,y_min)`.
- **[Kodla doğrulandı]** Legacy search velocity nav frame’de hesaplanır, yalnız `SEARCH_TARGET` içinde mission geofence ile clamp edilir, sonra local velocity’ye çevrilip `/drone/cmd_velocity` yayınlanır. Field search velocity LOCAL_NED olarak yayınlanır; eski axis-aligned mission clamp uygulanmaz. SafetyMonitor ve harici Mission Planner/FC geofence sınırlamaları ayrı kalır.

Search velocity call chain:

1. `MissionManagerNode._act_for_state(SEARCH_TARGET)` local telemetry’den `local_position.x/y` okur.
2. `CoordinateFrameMapper.nav_xy_from_local()` ile mission nav XY’ye çevirir.
3. İlk girişte `LawnmowerSearchPattern.start_from_x_max_is_nearest(nav_x, nav_y)` sadece ilk lane’in `(x_max,y_min)` ve `(x_min,y_min)` endpoint mesafelerini karşılaştırır.
4. `LawnmowerSearchPattern.next_velocity_from_start()` aktif waypoint’e göre `search_index,vx,vy` üretir. İlk waypoint’e giderken diagonal olabilir; sonraki segmentlerde axis-aligned velocity döndürür.
5. X ekseni baskın ve `abs(vx)>0.05` ise `alignment_forward_sign` güncellenir; align controller bu işareti kullanır.
6. `Geofence.clamp_velocity(nav_x,nav_y,vx,vy)` sadece mission search rectangle sınırına doğru giden bileşeni sıfırlar.
7. `CoordinateFrameMapper.local_velocity_from_nav()` local NED XY’ye çevirir.
8. `/drone/cmd_velocity` JSON publish edilir; `vz` `_restore_search_altitude_vz()` ile altitude restore için eklenir.

`TARGET_CANDIDATE`, `TARGET_ALIGN`, `TARGET_VERIFY` hızları `AlignmentController.velocity_from_center()` üzerinden gelir ve bu mission geofence clamp’inden geçmez.

## Geofence iki ayrı katman

- **[Kodla doğrulandı]** Mission-side geofence search rectangle ile aynıdır ve sadece SEARCH velocity clamp için kullanılır.
- **[Kodla doğrulandı]** SafetyMonitor geofence ayrı config kullanır: `x=-45..145`, `y=-25..25`, warning/hard margin.
- **[Kodla doğrulandı]** SafetyMonitor `/safety/status` içinde `status,x,y,local_x,local_y,coordinate_frame,timestamp` yayınlar; mission yalnız `status` okur.
- **[Kodla doğrulandı]** Yalnız `VIOLATION` FAILSAFE tetikler; `WARNING` ve `DISABLED` state machine’i durdurmaz.
- **[Kodla doğrulandı]** Uçuş kontrolcüsüne veya Mission Planner’a geofence upload/configure eden kod yoktur.

| Katman | Kod/config | Alan | Etki | Mission tüketimi |
|---|---|---|---|---|
| Mission search clamp | `MissionManagerNode.geofence`, `Geofence.clamp_velocity()`; `mission.yaml search_x/y_*` | `x=0..100`, `y=-12..12` | Yalnız `SEARCH_TARGET` içindeki nav velocity bileşenlerini sınırda sıfırlar | İçsel; `/safety/status` değildir. |
| Safety monitor | `SafetyMonitorNode`, `mission.yaml safety_monitor_node` | `x=-45..145`, `y=-25..25`, marginler | `/safety/status` `OK/WARNING/VIOLATION/DISABLED` yayınlar | Mission sadece `status` alanını okur; sadece `VIOLATION` FAILSAFE. |
| Flight controller geofence | Repoda kod yok | **[Repo’dan çıkarılamaz]** | ArduPilot/Mission Planner tarafında ayrıca kurulmuş olabilir veya olmayabilir | Runtime kodu upload/config yapmaz. |

> ⚠️ Align/verify hızları mission geofence ile clamp edilmez. Safety `VIOLATION` raporladığında failsafe devreye girebilir; warning yalnız gözlemseldir.

## Dört-köşe / GPS / polygon tasarım notu

**[Kodla doğrulandı]** WGS84 dosya loader, `/drone/global_origin` tabanlı LOCAL_NED projeksiyon ve field-local frame katmanı vardır. **[Kodla doğrulandı]** MissionManager field configured olduğunda rotated-rectangle `u/v` bounding geometry ile lawnmower search kullanır. Genel arbitrary polygon coverage, polygon clipping/decomposition ve geofence redesign hâlâ implement edilmemiştir.

Rotated-rectangle dışı genel polygon desteği eklenirse muhtemel etkilenecek modüller:

- `CoordinateFrameMapper`: GPS/local/nav frame ilişkisi ve origin/rotation tanımı gerekir.
- `LawnmowerSearchPattern` / field wrapper: `u/v` bounding rectangle yerine polygon-aware lane clipping gerekir.
- `Geofence`: `check()` ve `clamp_velocity()` rectangle varsayımını bırakmalı veya yeni polygon sınıfı eklenmeli.
- `MissionManagerNode._search_status()` ve state publish JSON’u: `search_target`, `search_axis`, `search_start` semantics değişebilir.
- `SafetyMonitorNode`: safety polygon ile mission search polygon aynı mı ayrı mı karar verilmeli.
- `target_specs_json` ve `payload_metrics`: target center koordinatlarının hangi frame’de olduğu netleştirilmeli.
- GCS/FC entegrasyonu: Repo içinde FC geofence upload yok; dört köşe kullanıcı akışı Mission Planner/QGC/ROS arasında tasarlanmalı.

Somut implikasyon: Mevcut field search dört köşeden türetilen rotated `u/v` bounding rectangle ile sınırlıdır; arbitrary polygon coverage veya safety/geofence polygon sınırı anlamına gelmez.
