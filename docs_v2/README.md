# ASFLY teknik referans v2

Bu dizin, gelecek Chef/Researcher/Coder oturumları ve proje geliştiricileri için **kodla doğrulanmış teknik referans** olarak oluşturuldu. `docs/` içeriğinin yeniden yazımı değildir.

## Kapsam ve kaynak politikası

- **[Kodla doğrulandı]**: İlgili Python/launch/config dosyası okunarak yazılmış gerçekler.
- **[Mevcut-docs iddiası, kodla doğrulandı]**: Eski dokümanlarda geçen ve kaynak kodla teyit edilen bilgi.
- **[Docs-only / bağlam]**: Repo içindeki doküman veya yorumlarda var, runtime kodundan tek başına çıkarılamaz.
- **[Repo’dan çıkarılamaz]**: Bu repoda kanıtı olmayan, varsayım yapılmaması gereken alan.
- **[Donanımda doğrulanmadı]**: Gerçek kamera/Pixhawk/servo/model ile test gerektiren davranış.

Repository root içinde `AGENTS.md` vardır ve bu çalışma öncesinde okunmuştur. Mevcut `docs/` ve README dosyaları bağlamdır; otorite kaynak kod, aktif launch dosyaları ve tüketilen config anahtarlarıdır. `build/`, `install/`, `log/` ve paketlenmiş kopyalar stale olabilir.

Source-of-truth özeti: `setup.py` top-level `vision/`, `control/`, `utils/` ve `config.py` modüllerini paketler; bu dosyalar aktif runtime bağımlılığıdır. Launch profillerinde default davranış yalnız node defaultlarından değil, verilen YAML ve launch param override’larından oluşur.

## Hızlı mimari harita

Aktif ROS entry point’leri `setup.py` içindedir: `perception_node`, `fusion_node`, `mission_manager_node`, `mavlink_bridge_node`, `safety_monitor_node`, `debug_viewer_node`, `mission_video_recorder_node`, `camera_frame_repeater_node`, `mission_console_node`.

Ana zincir:

`camera -> perception_node -> /perception/raw_detections -> fusion_node -> /fusion/target -> mission_manager_node -> /drone/cmd_* -> mavlink_bridge_node -> MAVLink`

`safety_monitor_node` `/drone/local_position` üzerinden `/safety/status` yayınlar. Console/recorder/debug gözlemseldir.

Önemli hızlı uyarılar:

- Topic payload’larının çoğu `std_msgs/String` içinde JSON’dur; custom ROS message değildir.
- `/camera/raw` karar/algı stream’i, `/camera` display/recording repeater stream’i olarak ayrılmıştır.
- `field_mission.launch.py` autostart default false; `mission.launch.py` override etmediği için mission node default true kalır.
- `mission.yaml end_action`, `mavlink*.yaml mode` anahtarları runtime’da beklenen şekilde tüketilmeyebilir; ilgili detay sayfalarına bakılmalı.

## Bu dizin nasıl kullanılmalı?

1. Runtime sınırları için [source_of_truth_and_runtime_boundaries.md](source_of_truth_and_runtime_boundaries.md).
2. Topic/launch/JSON sözleşmeleri için [runtime_architecture_and_topics.md](runtime_architecture_and_topics.md).
3. Algı-füzyon değişiklikleri için [perception_fusion_opencv_only.md](perception_fusion_opencv_only.md).
4. Görev/payload davranışı için [mission_state_payload.md](mission_state_payload.md).
5. Koordinat, arama, geofence için [coordinates_search_geofence.md](coordinates_search_geofence.md).
6. MAVLink saha entegrasyonu için [mavlink_control_field_integration.md](mavlink_control_field_integration.md).
7. Config/test envanteri için [config_and_tests_reference.md](config_and_tests_reference.md).
8. Bilinen riskler için [risks_unknowns_and_future_change_notes.md](risks_unknowns_and_future_change_notes.md).

> Doğrulama notu: Gazebo/SITL çalıştırılmadı ve bu dokümanın kabul kriteri olarak kullanılmamalıdır. Donanım doğrulaması iddia edilmez.
