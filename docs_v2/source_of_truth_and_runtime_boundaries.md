# Source of truth ve runtime sınırları

## Otorite kaynaklar

- **[Kodla doğrulandı]** Aktif kaynak dizinleri: `teknofest_iha/`, top-level `vision/`, `control/`, `utils/`, `config.py`, `config/*.yaml`, `launch/*.py`, `setup.py`, `scripts/` ve mevcut `docs/` bağlamı.
- **[Kodla doğrulandı]** `setup.py` paketleri `teknofest_iha`, `vision`, `control`, `utils` ve `py_modules=["config"]` olarak kuruyor. Bu nedenle top-level `vision/`, `control/`, `utils/`, `config.py` yalnızca legacy değil, aktif runtime bağımlılığıdır.
- **[Kodla doğrulandı]** Generated/stale-prone: `build/`, `install/`, `log/`, `teknofest_iha/install/`. Bu dizinler izleniyor olabilir ve yanıltabilir; aktif davranış için kaynak dosyalar tercih edilmeli.
- **[Çalışma kuralı]** Repository root içinde `AGENTS.md` vardır ve bu çalışma öncesinde okunmuştur. Dokümantasyon değişiklikleri yalnız `docs_v2/` altında tutulmalıdır.

Mevcut `docs/`, README’ler, runbook’lar ve script yorumları değerli bağlamdır; ancak runtime davranışı için son söz değildir. Özellikle launch+config+source birlikte okunmadan “default” iddiası verilmemelidir (`field_mission` autostart false override vs `mission.launch` node default true gibi).

## Aktif entry point’ler

`setup.py` `console_scripts`:

- `perception_node = teknofest_iha.nodes.perception_node:main`
- `fusion_node = teknofest_iha.nodes.fusion_node:main`
- `mission_manager_node = teknofest_iha.nodes.mission_manager_node:main`
- `mavlink_bridge_node = teknofest_iha.nodes.mavlink_bridge_node:main`
- `safety_monitor_node = teknofest_iha.nodes.safety_monitor_node:main`
- `debug_viewer_node`, `mission_video_recorder_node`, `camera_frame_repeater_node`, `mission_console_node`

## Legacy vs aktif domain modülleri

- **[Kodla doğrulandı]** `teknofest_iha/adapters/opencv_adapter.py` doğrudan `vision.opencv_detector.OpenCVDetector` kullanır.
- **[Kodla doğrulandı]** `teknofest_iha/adapters/fusion_adapter.py` `control.state_machine`, `control.payload_logic`, `vision.fusion`, `config.py` kullanır.

## Runtime sınırı hızlı linkleri

- Topic/launch zinciri: [runtime_architecture_and_topics.md](runtime_architecture_and_topics.md)
- Algı/fusion evidence sınırları: [perception_fusion_opencv_only.md](perception_fusion_opencv_only.md)
- Mission state ve payload sınırı: [mission_state_payload.md](mission_state_payload.md)
- Koordinat/geofence sınırı: [coordinates_search_geofence.md](coordinates_search_geofence.md)
- MAVLink saha sınırı: [mavlink_control_field_integration.md](mavlink_control_field_integration.md)
- Config/test gerçekleri: [config_and_tests_reference.md](config_and_tests_reference.md)
- Risk register: [risks_unknowns_and_future_change_notes.md](risks_unknowns_and_future_change_notes.md)

## docs_v2 doğrulama etiketleri

Bu dosyalarda her iddia etiketlenmese bile varsayılan kabul: aktif kod/config/launch incelenerek yazılmıştır. Donanım, model uyumluluğu ve uçuş kontrolcü kabul/ret davranışları **[Donanımda doğrulanmadı]** sayılır.

`Repo’dan çıkarılamaz` etiketi, mevcut repoda kanıtı bulunmayan veya ancak saha donanımı/GCS/FC konfigürasyonu ile anlaşılabilecek konular için kullanılır. Bu etiket varsayım yapılmaması gerektiğini ifade eder; davranışın imkânsız olduğunu kanıtlamaz.
