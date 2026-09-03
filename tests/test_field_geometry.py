import json
import math

from teknofest_iha.core.field_geometry import (
    EARTH_RADIUS_M,
    FieldConfigError,
    LocalPoint,
    WGS84Corner,
    build_field_geometry,
    load_mission_field,
    wgs84_to_ned_xy,
)


ORIGIN = {"lat_deg": 41.0, "lon_deg": 29.0, "alt_m": 100.0}


def _approx(actual, expected, abs_tol=1e-9, rel_tol=1e-9):
    if isinstance(actual, tuple):
        return all(_approx(a, e, abs_tol, rel_tol) for a, e in zip(actual, expected))
    return abs(actual - expected) <= max(abs_tol, rel_tol * max(abs(actual), abs(expected)))


def _assert_raises(exc_type, func, *args):
    try:
        func(*args)
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def _write_field(tmp_path, payload):
    path = tmp_path / "mission_field.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _corner_from_ned(x, y, origin=ORIGIN):
    lat = origin["lat_deg"] + math.degrees(x / EARTH_RADIUS_M)
    lon = origin["lon_deg"] + math.degrees(y / (EARTH_RADIUS_M * math.cos(math.radians(origin["lat_deg"]))))
    return WGS84Corner(lat=lat, lon=lon)


def _rectangle_corners(length_m, width_m, angle_deg=0.0):
    angle = math.radians(angle_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -math.sin(angle), math.cos(angle)
    points = []
    for u, v in [(-length_m / 2, -width_m / 2), (length_m / 2, -width_m / 2), (length_m / 2, width_m / 2), (-length_m / 2, width_m / 2)]:
        points.append(_corner_from_ned(u * ux + v * vx, u * uy + v * vy))
    return points


def test_valid_mission_field_parse(tmp_path):
    corners = [{"lat": 41.0, "lon": 29.0}, {"lat": 41.0, "lon": 29.001}, {"lat": 41.001, "lon": 29.001}, {"lat": 41.001, "lon": 29.0}]
    path = _write_field(tmp_path, {"version": 1, "coordinate_system": "WGS84", "corners": corners})

    parsed = load_mission_field(path)

    assert len(parsed) == 4
    assert parsed[0] == WGS84Corner(lat=41.0, lon=29.0)


def test_invalid_mission_field_rejects(tmp_path):
    payloads = [
        {"version": 2, "coordinate_system": "WGS84", "corners": [{"lat": 0, "lon": 0}] * 4},
        {"version": 1, "coordinate_system": "LOCAL_NED", "corners": [{"lat": 0, "lon": 0}] * 4},
        {"version": 1, "coordinate_system": "WGS84", "corners": [{"lat": 91, "lon": 0}] * 4},
        {"version": 1, "coordinate_system": "WGS84", "corners": [{"lat": 0, "lon": 181}] * 4},
        {"version": 1, "coordinate_system": "WGS84", "corners": [{"lat": 0}] * 4},
    ]
    for index, payload in enumerate(payloads):
        path = tmp_path / f"mission_field_{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        _assert_raises(FieldConfigError, load_mission_field, path)


def test_projection_origin_is_zero_and_axes_increase():
    assert _approx(wgs84_to_ned_xy(41.0, 29.0, 41.0, 29.0), (0.0, 0.0), abs_tol=1e-9)

    north, east = wgs84_to_ned_xy(41.0, 29.0, 41.0001, 29.0)
    assert north > 0.0
    assert abs(east) < 1e-6

    north, east = wgs84_to_ned_xy(41.0, 29.0, 41.0, 29.0001)
    assert east > 0.0
    assert abs(north) < 1e-6


def test_geometry_builds_for_different_field_sizes():
    for length, width in [(20.0, 20.0), (50.0, 10.0), (100.0, 30.0), (120.0, 40.0)]:
        geometry = build_field_geometry(_rectangle_corners(length, width), ORIGIN)

        assert _approx(geometry.area_m2, length * width, rel_tol=0.01)
        assert _approx(geometry.long_length_m, max(length, width), rel_tol=0.01)
        assert _approx(geometry.short_length_m, min(length, width), rel_tol=0.01)


def test_rotated_rectangle_axes_are_sensible():
    geometry = build_field_geometry(_rectangle_corners(120.0, 40.0, angle_deg=30.0), ORIGIN)

    assert _approx(geometry.long_length_m, 120.0, rel_tol=0.01)
    assert _approx(geometry.short_length_m, 40.0, rel_tol=0.01)
    assert abs(geometry.u_axis[0] * geometry.v_axis[0] + geometry.u_axis[1] * geometry.v_axis[1]) < 1e-9


def test_duplicate_corner_invalid():
    corners = [_corner_from_ned(0, 0), _corner_from_ned(0, 0.05), _corner_from_ned(10, 0), _corner_from_ned(10, 10)]

    _assert_raises(FieldConfigError, build_field_geometry, corners, ORIGIN)


def test_crossed_user_order_is_normalized_when_rectangle_is_valid():
    corners = _rectangle_corners(50.0, 10.0)
    crossed_order = [corners[0], corners[2], corners[1], corners[3]]

    geometry = build_field_geometry(crossed_order, ORIGIN)

    assert _approx(geometry.area_m2, 500.0, rel_tol=0.01)


def test_degenerate_or_concave_geometry_invalid():
    corners = [_corner_from_ned(0, 0), _corner_from_ned(10, 0), _corner_from_ned(5, 2), _corner_from_ned(0, 10)]

    _assert_raises(FieldConfigError, build_field_geometry, corners, ORIGIN)


def test_field_local_roundtrip():
    geometry = build_field_geometry(_rectangle_corners(120.0, 40.0, angle_deg=25.0), ORIGIN)
    point = LocalPoint(12.3, -4.5)

    u, v = geometry.ned_to_field_uv(point)
    roundtrip = geometry.field_uv_to_ned(u, v)

    assert _approx(roundtrip.x, point.x, abs_tol=1e-9)
    assert _approx(roundtrip.y, point.y, abs_tol=1e-9)


def test_missing_origin_invalid():
    _assert_raises(FieldConfigError, build_field_geometry, _rectangle_corners(20.0, 20.0), {"lat_deg": None, "lon_deg": 29.0})


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        test_valid_mission_field_parse(Path(tmp))
        test_invalid_mission_field_rejects(Path(tmp))
    test_projection_origin_is_zero_and_axes_increase()
    test_geometry_builds_for_different_field_sizes()
    test_rotated_rectangle_axes_are_sensible()
    test_duplicate_corner_invalid()
    test_crossed_user_order_is_normalized_when_rectangle_is_valid()
    test_degenerate_or_concave_geometry_invalid()
    test_field_local_roundtrip()
    test_missing_origin_invalid()
