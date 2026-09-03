# Mission state ve payload referansı

> Kaynak sınırı: `teknofest_iha/nodes/mission_manager_node.py`, `teknofest_iha/core/{state_machine,mission_states,target_selection,payload_controller,payload_metrics,alignment_controller}.py`, `teknofest_iha/interfaces/drone_models.py`, `config/mission.yaml` incelendi. Servo/Pixhawk/payload mekaniği donanımda doğrulanmadı.

## Mission manager callback ve topic’leri

**[Kodla doğrulandı]** `mission_manager_node.py` abonelikleri: `/fusion/target`, `/drone/state`, `/drone/local_position`, `/drone/altitude`, `/safety/status`, `/mission/cmd_start`. Yayınları: `/drone/cmd_mode`, `/drone/cmd_arm`, `/drone/cmd_takeoff`, `/drone/cmd_velocity`, `/drone/cmd_land`, `/drone/cmd_drop`, `/mission/state`, `/mission/event`.

## Start/autostart davranışı

- **[Kodla doğrulandı]** Node default `autostart=True`.
- **[Kodla doğrulandı]** `config/mission.yaml` autostart içermez.
- **[Kodla doğrulandı]** `field_mission.launch.py` autostart default false override eder; obs profili de benzer bağlamda false olabilir. `mission.launch.py` override etmez; node default true geçerlidir.

## MissionStateMachine geçişleri

Aktif geçiş: `INIT -> WAIT_FOR_CAMERA -> CONNECT_MAVLINK -> SET_GUIDED -> ARM -> TAKEOFF -> SEARCH_TARGET -> TARGET_CANDIDATE -> TARGET_ALIGN -> TARGET_VERIFY -> DROP_TARGET -> POST_DROP_HOVER -> next SEARCH_TARGET or RETURN_HOME -> MISSION_COMPLETE`.

- **[Kodla doğrulandı]** Herhangi bir state’te `safety_level == VIOLATION` => `FAILSAFE`.
- **[Kodla doğrulandı]** `LAND` enum/action var ama state machine geçişi LAND’e ulaşmıyor; legacy `SEARCH_BLUE/BLUE_*` enumları da aktif geçişte kullanılmıyor.
- **[Kodla doğrulandı]** `RETURN_HOME` tamamlanması `drone_state.mode == RTL` ile olur.
- **[Kodla doğrulandı]** `config/mission.yaml end_action: rtl` declare edilir ama `MissionStateMachine.update()` içinde okunmaz; runtime son akış `RETURN_HOME` ve `/drone/cmd_mode` `RTL` komutudur.

| State | Çıkış koşulu | Sonraki state | MissionManager aksiyonu |
|---|---|---|---|
| `INIT` | Her update | `WAIT_FOR_CAMERA` | Sadece state publish. |
| `WAIT_FOR_CAMERA` | `camera_ready = last_fusion is not None` | `CONNECT_MAVLINK` | Perception/fusion yoksa bekler. |
| `CONNECT_MAVLINK` | `drone_state.connected` | `SET_GUIDED` | Köprü telemetry beklenir. |
| `SET_GUIDED` | `drone_state.mode == GUIDED` | `ARM` | `/drone/cmd_mode` periyodik `set_mode GUIDED`. |
| `ARM` | `drone_state.armed` | `TAKEOFF` | Gerekirse mode tekrar, `/drone/cmd_arm`. |
| `TAKEOFF` | `abs(altitude-takeoff_altitude) <= altitude_tolerance` | `SEARCH_TARGET` | Gerekirse mode/arm, `/drone/cmd_takeoff`. |
| `SEARCH_TARGET` | `target is not None` | `TARGET_CANDIDATE` | Lawnmower velocity; sadece burada mission geofence clamp. |
| `TARGET_CANDIDATE` | target yok | `SEARCH_TARGET` | Seçili hedef varsa align velocity. |
| `TARGET_CANDIDATE` | target var | `TARGET_ALIGN` | Seçili hedef varsa align velocity. |
| `TARGET_ALIGN` | target yok | `SEARCH_TARGET` | Align velocity. |
| `TARGET_ALIGN` | `target_centered` | `TARGET_VERIFY` | Align velocity. |
| `TARGET_VERIFY` | target yok | `SEARCH_TARGET` | Centered+stable+yüksekse descent `vz>0`. |
| `TARGET_VERIFY` | `target_centered and target_locked` | `DROP_TARGET` | `target_locked` burada mission hesaplı `drop_ready` anlamındadır. |
| `DROP_TARGET` | `drop_done` | `POST_DROP_HOVER` | Koşullar korunuyorsa drop event/cmd yayınlar. |
| `DROP_TARGET` | target yok / centered değil / locked-drop-ready değil | `SEARCH_TARGET` / `TARGET_ALIGN` / `TARGET_VERIFY` | Drop komutu henüz işaretlenmediyse mevcut arama-hizalama-doğrulama akışına geri döner. |
| `POST_DROP_HOVER` | hover süresi ve altitude restore | sonraki hedef için `SEARCH_TARGET` veya `RETURN_HOME` | Hover/restore velocity. |
| `RETURN_HOME` | `drone_state.mode == RTL` | `MISSION_COMPLETE` | `/drone/cmd_mode` `RTL`. |
| Her state | `safety_level == VIOLATION` | `FAILSAFE` | Zero velocity + land periyodik. |

## MissionInputs mapping

`MissionManagerNode.on_timer()` saf state machine’e şu snapshot’ı verir:

| `MissionInputs` alanı | Runtime kaynağı | Not |
|---|---|---|
| `camera_ready` | `self.last_fusion is not None` | Sadece fusion packet alındı mı; kamera görüntü kalitesi doğrulamaz. |
| `mavlink_connected` | `/drone/state.connected` | Köprü heartbeat state’inden gelir. |
| `guided` | `/drone/state.mode == "GUIDED"` | `mavlink.yaml mode` default olarak kullanılmaz. |
| `armed` | `/drone/state.armed` | Heartbeat base_mode parse. |
| `altitude_m` | `_relative_altitude_m()` | `local_position.z < -0.05` ise `-z`, değilse `/drone/altitude.relative_m`. |
| `target` | `_selected_target(active_target)` | Fusion selected veya targets içinde active target. |
| `target_centered` | `AlignmentController.is_centered(center)` | `mission.yaml center_tolerance_px`. |
| `target_locked` | local `drop_ready` | `lock_stable and (!approach_enabled or drop_altitude_reached)`. Fusion `release_gate` değildir. |
| `safety_level` | `/safety/status.status` | Rich payload içinden yalnız bu string okunur. |
| `drop_done` | `not PayloadController.can_release(active_target)` | Mission payload set’i; bridge sonucu beklenmez. |
| `return_confirmed` | `/drone/state.mode == "RTL"` | ACK değil, telemetry mode kontrolü. |

## Target selection ve promotion

- **[Kodla doğrulandı]** Config primary `blue_square`, secondary `red_square`; ancak sıra katı değildir.
- **[Kodla doğrulandı]** `SEARCH_TARGET`/`TARGET_CANDIDATE` sırasında görünür ve unreleased hedef active slot’a taşınabilir.
- **[Kodla doğrulandı]** `TARGET_ALIGN`/`TARGET_VERIFY` sırasında active target hâlâ seçilebiliyorsa korunur; active target kaybolmuşsa görünür unreleased hedef active slot’a taşınabilir.
- **[Kodla doğrulandı]** `choose_visible_unreleased_target()` scoring: selected bonus, state priority, release/drop_ready bonus, confidence. Red görünür ve skoru yüksekse primary’den önce ele alınabilir.

Promotion mekanizması `MissionManagerNode._promote_visible_target()` ve `_move_target_to_active_slot()` içindedir. `target_sequence` tuple’ı runtime’da kalan hedefler içinde yeniden sıralanabilir; geçmişte release edilmiş hedefler `PayloadController.can_release()` ile elenir. Bu, “blue sonra red” gibi katı sıra varsayımını geçersiz kılar.

## Align/verify/drop

- **[Kodla doğrulandı]** `AlignmentController.velocity_from_center()` görüntü merkez hatasını nav-frame XY hızına çevirir; forward sign arama lane yönünden gelir.
- **[Kodla doğrulandı]** Mission lock şartı: `target_state in LOCKED/DROP_READY` veya `drop_perception_gate`, centered, confidence >= `lock_min_confidence`, aynı hedef için `lock_seconds` stabil.
- **[Kodla doğrulandı]** Drop readiness: lock stable ve `approach_enabled` false veya relative altitude <= `drop_altitude_m`.
- **[Kodla doğrulandı]** Descent yalnız `TARGET_VERIFY` + centered + lock_stable + drop altitude üstündeyken yapılır. NED: descent `vz` pozitif, climb `vz` negatif.
- **[Kodla doğrulandı]** Drop event aynı JSON’u `/mission/event` ve `/drone/cmd_drop` içine yayınlar; mission manager payload’ı bridge dry-run sonucunu beklemeden released işaretler.
- **[Kodla doğrulandı]** `payload_dry_run=true` default config: MAVLink bridge `DROP_DRY_RUN` status yayınlar, servo komutu göndermez; mission yine ilerler.
- **[Kodla doğrulandı]** Fusion `release_gate` mission drop için doğrudan gate değildir. Mission `_target_locked()` ve altitude/approach mantığıyla kendi `lock_stable/drop_ready` hesabını yapar.

Drop/payload JSON alanları (`command_json("drop_payload", ...)`):

| Alan | Kaynak | Anlam |
|---|---|---|
| `command` | Sabit | `drop_payload`. |
| `timestamp` | `command_json()` | Publish zamanı. |
| `target_type` | active target | Örn. `blue_square`, `red_square`. |
| `dry_run` | `payload_dry_run` | True ise bridge servo göndermez. |
| `servo` | `payload_servo` | Default/YAML: 9. |
| `pwm` | `payload_pwm` | Default/YAML: 1900. |
| `reset_pwm` | `payload_reset_pwm` | Default/YAML: 1100. |
| `hold_seconds` | `payload_hold_seconds` | Default/YAML: 0.8. |
| `drop_estimate` | `_drop_estimate()` opsiyonel | `target_specs_json` varsa payload metrics sonucu eklenir. Balistik doğruluk donanımda doğrulanmadı. |

Release sırası: `PayloadController.mark_released()` önce çağrılır, sonra event/cmd publish edilir. Bridge dry-run veya hata sonucu mission tarafından beklenmez. Bu, dry-run modda testte görevin ilerlemesini sağlar; gerçek servo başarısını kanıtlamaz.

`DROP_TARGET` escape davranışı: drop yerel payload state’inde tamamlandıysa `POST_DROP_HOVER` sürer. Drop henüz tamamlanmadıysa ve target/centered/locked-drop-ready şartlarından biri kaybolursa state machine sırasıyla `SEARCH_TARGET`, `TARGET_ALIGN` veya `TARGET_VERIFY` akışına geri döner; şartlar hâlâ korunuyorsa `DROP_TARGET` içinde kalır ve aynı tick’te mevcut drop publish/mark-release yolu çalışabilir.
