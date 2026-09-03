from teknofest_iha.adapters.mavlink_adapter import MavlinkAdapter
from teknofest_iha.interfaces.drone_models import Altitude, DroneState, GlobalOrigin, GlobalPosition, GpsStatus, HomePosition, LocalPosition


class DummyMessage:
    def __init__(self, msg_type, **fields):
        self._msg_type = msg_type
        for key, value in fields.items():
            setattr(self, key, value)

    def get_type(self):
        return self._msg_type


class DummyMaster:
    def __init__(self, messages):
        self._messages = list(messages)

    def recv_match(self, blocking=False, timeout=0):
        if not self._messages:
            return None
        return self._messages.pop(0)


def _adapter():
    adapter = MavlinkAdapter.__new__(MavlinkAdapter)
    adapter.master = DummyMaster([])
    adapter.state = DroneState()
    adapter.local_position = LocalPosition()
    adapter.altitude = Altitude()
    adapter.global_position = GlobalPosition()
    adapter.gps_status = GpsStatus()
    adapter.global_origin = GlobalOrigin()
    adapter.home_position = HomePosition()
    adapter.last_gcs_heartbeat_s = 0.0
    adapter._send_gcs_heartbeat = lambda *args, **kwargs: None
    return adapter


def test_gps_dataclass_json_roundtrips():
    global_position = GlobalPosition(lat_deg=41.1, lon_deg=29.2, relative_m=12.3, amsl_m=102.4, timestamp=1.0)
    gps_status = GpsStatus(fix_type=3, satellites_visible=10, eph=123.0, epv=456.0, hdop=None, timestamp=2.0)
    global_origin = GlobalOrigin(lat_deg=41.0, lon_deg=29.0, alt_m=100.0, timestamp=3.0)
    home_position = HomePosition(lat_deg=41.2, lon_deg=29.3, alt_m=105.0, x=1.0, y=2.0, z=-3.0, timestamp=4.0)

    assert GlobalPosition.from_json(global_position.to_json()) == global_position
    assert GpsStatus.from_json(gps_status.to_json()) == gps_status
    assert GlobalOrigin.from_json(global_origin.to_json()) == global_origin
    assert HomePosition.from_json(home_position.to_json()) == home_position


def test_global_position_int_updates_altitude_and_global_position():
    adapter = _adapter()
    adapter._handle_message(DummyMessage("GLOBAL_POSITION_INT", lat=411234567, lon=291234567, relative_alt=12345, alt=102345))

    assert adapter.altitude.relative_m == 12.345
    assert adapter.altitude.amsl_m == 102.345
    assert adapter.global_position.lat_deg == 41.1234567
    assert adapter.global_position.lon_deg == 29.1234567
    assert adapter.global_position.relative_m == 12.345
    assert adapter.global_position.amsl_m == 102.345


def test_gps_raw_int_updates_gps_status_with_raw_eph_epv():
    adapter = _adapter()
    adapter._handle_message(DummyMessage("GPS_RAW_INT", fix_type=3, satellites_visible=12, eph=140, epv=220))

    assert adapter.gps_status.fix_type == 3
    assert adapter.gps_status.satellites_visible == 12
    assert adapter.gps_status.eph == 140.0
    assert adapter.gps_status.epv == 220.0
    assert adapter.gps_status.hdop is None


def test_global_origin_and_home_position_parsing():
    adapter = _adapter()
    adapter._handle_message(DummyMessage("GPS_GLOBAL_ORIGIN", latitude=410000000, longitude=290000000, altitude=99000))
    adapter._handle_message(DummyMessage("HOME_POSITION", latitude=411000000, longitude=291000000, altitude=101000, x=1, y=2, z=-3))

    assert adapter.global_origin.lat_deg == 41.0
    assert adapter.global_origin.lon_deg == 29.0
    assert adapter.global_origin.alt_m == 99.0
    assert adapter.home_position.lat_deg == 41.1
    assert adapter.home_position.lon_deg == 29.1
    assert adapter.home_position.alt_m == 101.0
    assert adapter.home_position.x == 1.0
    assert adapter.home_position.y == 2.0
    assert adapter.home_position.z == -3.0


def test_read_messages_returns_cached_gps_telemetry():
    adapter = _adapter()
    adapter.master = DummyMaster([DummyMessage("GPS_RAW_INT", fix_type=4, satellites_visible=9, eph=100, epv=200)])

    status = adapter.read_messages(timeout_s=0.0)

    assert status.state is adapter.state
    assert status.local_position is adapter.local_position
    assert status.altitude is adapter.altitude
    assert status.global_position is adapter.global_position
    assert status.gps_status.fix_type == 4
    assert status.global_origin is adapter.global_origin
    assert status.home_position is adapter.home_position
