# State Machines

Bu projede iki ana state machine vardir:

1. Target Fusion State Machine (`control/state_machine.py`)
2. Mission State Machine (`teknofest_iha/core/state_machine.py`)

Algilama guveni ile ucus/gorev icrasi ayni sey degildir; bu nedenle state
machine'ler ayridir.

## Target Fusion State Machine

State'ler:

```text
SEARCH -> CANDIDATE -> TRACKING / UNSTABLE / LOCKED
```

- `SEARCH`: hedef yok veya OpenCV hedef adayi uretmedi.
- `CANDIDATE`: yeni dogrudan hedef gozlemi var; warm-up beklenir.
- `TRACKING`: hedef bilgisi var ama lock kosulu saglanmiyor.
- `UNSTABLE`: kararsiz hedef durumu icin ayrilmis state; aktif OpenCV-only
  path'te dogrulanmamis tracker/Kalman gozlemleri lock'a ilerlemez.
- `LOCKED`: dogrudan contour/shape-valid OpenCV gozlemi ve confidence esigi
  yeterlidir.

Lock kosulu:

```text
perception_validated == true
fusion_confidence >= FUSION_CONF_THRESH
```

Tracker/Kalman continuity gozlemleri `perception_validated=false` kalir; lock
counter ilerletmez ve payload release icin validation saglamaz.

## Release Gate

`release_gate` bir state degildir. Fusion'in mission manager'a verdigi algisal
izin sinyalidir; servo komutu degildir.

Kosul:

```text
perception_validated == true
fusion_confidence >= FUSION_CONF_THRESH
abs(error_x) <= CENTER_TOL_X
abs(error_y) <= CENTER_TOL_Y
lock_counter >= LOCK_MIN_FRAMES
```

Mission manager bu sinyali kendi centered/lock-time/drop-altitude kosullariyla
birlikte degerlendirir.

## Mission State Machine

Ana state'ler:

```text
INIT -> WAIT_FOR_CAMERA -> CONNECT_MAVLINK -> SET_GUIDED -> ARM -> TAKEOFF -> SEARCH_TARGET -> TARGET_CANDIDATE -> TARGET_ALIGN -> TARGET_VERIFY -> DROP_TARGET -> POST_DROP_HOVER -> RETURN_HOME -> MISSION_COMPLETE
```

`FAILSAFE`, safety violation veya kritik hata durumlari icindir.

Mission manager:

- search pattern velocity komutlari uretir,
- hedef gorulurse align/verify/drop akisina gecer,
- payload event ve `/drone/cmd_drop` yayinlar,
- tum hedeflerden sonra RTL ister.

Arm, takeoff, velocity, land/RTL ve servo/PWM komutlari MAVLink bridge uzerinden
ayri topic sozlesmeleriyle gider.

## OBS Terminal Stateflow

Aktif console cikti ornegi:

```text
[MISSION] state=SEARCH_TARGET  geofence=OK  lane=03
[SEARCH ] next_point=(100,-10)  target=red_square
[VISION ] opencv=DETECTED  validation=VALIDATED
[FUSION ] target=red_square  state=LOCKED  conf=0.91
[ALIGN  ] error_x=12  error_y=-8  center=OK
[GATE   ] release_gate=TRUE  lock_counter=10/10
[PAYLOAD] released=1/2  target=red_square
[MISSION] state=RESUME_SEARCH  next_target=blue_square
```
