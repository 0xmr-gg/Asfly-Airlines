# Perception ve fusion OpenCV-only durumu

> Kaynak sınırı: `teknofest_iha/nodes/perception_node.py`, `teknofest_iha/adapters/{opencv_adapter,fusion_adapter}.py`, top-level `vision/*`, `control/*`, `config.py`, `config/perception.yaml`, `config/fusion.yaml` incelendi. Gerçek kamera/Pixhawk/servo davranışı bu dokümanda doğrulanmaz.

- **[Kodla doğrulandı]** `perception_node` kamera görüntüsünü `OpenCVAdapter.detect()` ile işler ve raw packet olarak yalnız `frame_id`, `timestamp`, `opencv` alanlarını yayınlar.
- **[Kodla doğrulandı]** `RawDetectionPacket.from_json()` eski log/test girdilerindeki ekstra alanları yok sayacak kadar toleranslıdır; `to_json()` yeni packet içine yalnız aktif OpenCV sözleşmesini yazar.
- **[Kodla doğrulandı]** `FusionAdapter` her hedef için `TargetStateMachine` tutar, OpenCV detections listesinden hedefe göre seçim yapar ve `vision.fusion.fuse_detections()` sonucuna `perception_validated`, `target_state`, `release_gate`, `drop_ready`, `drop_perception_gate`, `lock_counter`, `unstable_counter` alanlarını ekler.
- **[Kodla doğrulandı]** `perception_validated()` doğrudan contour/shape-valid gözlemi doğrulanmış kabul eder; `tracker` ve `kalman` süreklilik gözlemleri kilit veya release doğrulaması sağlamaz.
- **[Kodla doğrulandı]** `compute_release_gate()` hala error, `perception_validated`, `FUSION_CONF_THRESH`, merkez toleransları ve `LOCK_MIN_FRAMES` şartlarını birlikte ister.

## Doğrulanmayanlar

- Gerçek kamera görüntülerinde OpenCV eşikleri ve şekil filtrelerinin saha performansı.
- Gerçek İHA üzerinde payload bırakma doğruluğu ve uçuş kontrolcü davranışı.
