# Riskler, bilinmeyenler ve gelecek değişiklik notları

## Mevcut docs ile bilinen uyumsuzluklar

- **[Orta]** Autostart default: node default true; field launch false override eder. Eski dokümanlarda default false genellemesi hatalı olabilir.
- **[Orta]** `mission.yaml end_action` config’te var ama aktif state machine paramı kullanmıyor; final runtime RTL akışıyla ilerliyor.
- **[Yüksek]** Fusion `release_gate` mission drop için doğrudan gate değildir; mission kendi centered/lock/drop-altitude koşulunu kullanır.
- **[Orta]** Target order katı değil; scoring/promotion red’i primary’den önce işletebilir.
- **[Düşük]** `/safety/status` eski docs’tan daha zengin JSON taşır; mission ise yalnız `status` alanını okur.
- **[Yüksek]** İki geofence vardır: mission clamp ve safety monitor; FC/Mission Planner geofence otomasyonu yok.
- **[Orta]** `/drone/cmd_position` bridge consumer’ı eski dokümanlarda görünmeyebilir; mission producer yoktur.
- **[Orta]** Field mission MAVLink config default’u `mavlink_gcs_router.yaml`.
- **[Düşük]** Bazı script/dokümanlarda hardcoded stale path olabilir; generated `build/install/log` daha da yanıltıcı olabilir.
- **[Orta]** Kamera topic ambiguity: node default `/camera`, YAML `/camera/raw`; launch yorumlarına göre `/camera/raw` karar stream’i, `/camera` display/recording repeat.
- **[Orta]** OpenCV-only doğrulamanın gerçek saha görüntülerindeki güvenilirliği donanım/kamera olmadan doğrulanamaz.
- **[Orta]** `config/mavlink*.yaml mode` var ama startup/default set_mode davranışı değil.

## Cross-cutting riskler

> ✅ **[Kodla giderildi]** `DROP_TARGET` deadlock riski: drop tamamlanmadan target/center/locked-drop-ready koşulu kaybolursa state machine arama, hizalama veya doğrulama akışına geri döner; koşullar korunuyorsa drop publish yolu için `DROP_TARGET` içinde kalır.

> ⚠️ **[Yüksek]** Align/verify hızları mission geofence clamp dışında; safety yalnız VIOLATION’da state machine’i failsafe yapar.

> ⚠️ **[Orta]** JSON/String topic’lerde şema validasyonu sınırlı; hatalı alanlar runtime exception veya sessiz yanlış davranış yaratabilir.

> ⚠️ **[Yüksek]** MAVLink tarafında COMMAND_ACK/battery/GPS/EKF/failsafe parse yok; connected/healthy algısı eksik olabilir.

> ⚠️ **[Yüksek]** Arm/takeoff/velocity/MAVLink/geofence/payload davranışları gerçek araç olmadan doğrulanmış sayılmamalı; bu doküman donanım-verified iddiası taşımaz.

## Donanımda doğrulanmayanlar

Gerçek kamera topic/FPS/encoding, OpenCV CSRT varlığı, Pixhawk device/baud/mode/arming, servo channel/PWM/mekanik, FC geofence/manual setup, gerçek local NED hizalaması, `MAV_FRAME_LOCAL_NED` etkisi ve payload ballistics bu repodan doğrulanamaz.

## OpenCV-only algı için notlar

Aktif runtime model dosyası aramaz ve raw detection JSON içinde yalnız OpenCV gözlemlerini taşır. Payload release kriteri doğrudan contour/shape-valid OpenCV gözlemi, fusion confidence, merkez toleransı ve lock counter şartlarını birlikte istemeye devam eder. Tracker/Kalman süreklilik gözlemleri doğrulama sağlamaz.

## Dört-köşe search-area tasarımı

Mevcut implementasyon axis-aligned rectangle’dır. Dört köşe capture/polygon/GPS projection eklenirse şu kararlar netleşmeden kod yazılmamalı: koordinat kaynağı, origin anchoring, polygon içi lane üretimi, rotation, mission clamp vs safety geofence ayrımı, FC geofence upload gereksinimi ve GCS ile kullanıcı akışı.

Muhtemel tasarım notları:

- Dört köşe sadece UI/config formatı değildir; `CoordinateFrameMapper`, `LawnmowerSearchPattern`, `Geofence`, `SafetyMonitorNode`, `MissionManagerNode._search_status()` birlikte etkilenir.
- Mission geofence ve safety geofence aynı polygon mu farklı marginli polygon mu olmalı?
- FC geofence upload gerekiyorsa ayrı MAVLink param/mission protocol entegrasyonu gerekir; repoda mevcut kod yok.
- GPS köşeleri local NED’e çevrilecekse origin, heading/yaw ve projection kaynağı açıkça belirlenmeli.
- Rotated lawnmower velocity align controller’ın `alignment_forward_sign` varsayımını etkileyebilir.

## Doğrulama sınırı

Bu doküman kaynak kod/config/launch okuyarak hazırlandı. Gazebo/SITL kullanılmadı. Donanım-verified iddiası yoktur.
