import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from teknofest_iha.core.field_geometry import FieldGeometry, LocalPoint, WGS84Corner
from teknofest_iha.core.search_pattern import FieldLawnmowerSearchPattern, LawnmowerSearchPattern


def _approx(actual, expected, abs_tol=1e-9, rel_tol=1e-9):
    return abs(actual - expected) <= max(abs_tol, rel_tol * max(abs(actual), abs(expected)))


def _geometry(length_m, width_m, angle_deg=0.0):
    angle = math.radians(angle_deg)
    u_axis = (math.cos(angle), math.sin(angle))
    v_axis = (-math.sin(angle), math.cos(angle))
    corners = tuple(
        LocalPoint(u * u_axis[0] + v * v_axis[0], u * u_axis[1] + v * v_axis[1])
        for u, v in [
            (-length_m / 2, -width_m / 2),
            (length_m / 2, -width_m / 2),
            (length_m / 2, width_m / 2),
            (-length_m / 2, width_m / 2),
        ]
    )
    return FieldGeometry(
        corners_wgs84=(
            WGS84Corner(0.0, 0.0),
            WGS84Corner(0.0, 0.0),
            WGS84Corner(0.0, 0.0),
            WGS84Corner(0.0, 0.0),
        ),
        corners_ned=corners,
        center=LocalPoint(0.0, 0.0),
        u_axis=u_axis,
        v_axis=v_axis,
        long_length_m=length_m,
        short_length_m=width_m,
        edge_lengths_m=(length_m, width_m, length_m, width_m),
        area_m2=length_m * width_m,
        u_min=-length_m / 2,
        u_max=length_m / 2,
        v_min=-width_m / 2,
        v_max=width_m / 2,
    )


def test_lawnmower_waypoints_alternate_direction():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)
    assert pattern.waypoints() == [
        (0.0, -5.0),
        (10.0, -5.0),
        (10.0, 0.0),
        (0.0, 0.0),
        (0.0, 5.0),
        (10.0, 5.0),
    ]


def test_lawnmower_advances_after_passing_lane_endpoint():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)

    index, vx, vy = pattern.next_velocity(11.0, -5.0, 1, 2.0)

    assert index == 2
    assert vx == 0.0
    assert vy > 0.0


def test_lawnmower_advances_at_lane_endpoint_with_cross_track_error():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)

    index, vx, vy = pattern.next_velocity(9.2, -3.0, 1, 2.0)

    assert index == 2
    assert vx == 0.0
    assert vy > 0.0


def test_lawnmower_does_not_return_along_completed_lane():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)

    index, vx, vy = pattern.next_velocity(10.5, -0.1, 2, 2.0)

    assert index == 3
    assert vx < 0.0
    assert vy == 0.0


def test_lawnmower_horizontal_lane_has_no_lateral_velocity():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)

    index, vx, vy = pattern.next_velocity(4.0, -4.2, 1, 2.0)

    assert index == 1
    assert vx > 0.0
    assert vy == 0.0


def test_lawnmower_can_start_from_nearest_x_max_side():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)

    assert pattern.waypoints_from_nearest_start(9.0, -8.0) == [
        (10.0, -5.0),
        (0.0, -5.0),
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 5.0),
        (0.0, 5.0),
    ]


def test_nearest_start_avoids_crossing_to_far_lane_start():
    pattern = LawnmowerSearchPattern(0.0, 10.0, -5.0, 5.0, 5.0)

    index, vx, vy = pattern.next_velocity_from_start(10.0, -5.0, 0, 2.0, 0.5, start_from_x_max=True)

    assert index == 1
    assert vx < 0.0
    assert vy == 0.0


def test_axis_aligned_field_lawnmower_matches_legacy_waypoints():
    geometry = _geometry(10.0, 10.0)
    field_pattern = FieldLawnmowerSearchPattern(geometry, 5.0)
    legacy = LawnmowerSearchPattern(-5.0, 5.0, -5.0, 5.0, 5.0)

    assert field_pattern.waypoints_from_start(False) == legacy.waypoints_from_start(False)


def test_rotated_field_lanes_are_parallel_to_long_axis():
    geometry = _geometry(120.0, 40.0, angle_deg=30.0)
    pattern = FieldLawnmowerSearchPattern(geometry, 10.0)
    points = pattern.waypoints_from_start(False)

    for index in range(0, len(points), 2):
        dx = points[index + 1][0] - points[index][0]
        dy = points[index + 1][1] - points[index][1]
        length = math.hypot(dx, dy)
        lane_dot_u = (dx / length) * geometry.u_axis[0] + (dy / length) * geometry.u_axis[1]
        assert _approx(abs(lane_dot_u), 1.0, abs_tol=1e-9)


def test_field_lawnmower_endpoints_stay_inside_uv_bounds_for_sizes():
    for length, width in [(20.0, 20.0), (50.0, 10.0), (100.0, 30.0), (120.0, 40.0)]:
        geometry = _geometry(length, width, angle_deg=25.0)
        pattern = FieldLawnmowerSearchPattern(geometry, 5.0)

        for point in pattern.waypoints_from_start(False):
            u, v = geometry.ned_to_field_uv(point)
            assert geometry.u_min - 1e-9 <= u <= geometry.u_max + 1e-9
            assert geometry.v_min - 1e-9 <= v <= geometry.v_max + 1e-9


def test_field_lawnmower_nearest_start_uses_field_local_coordinates():
    geometry = _geometry(50.0, 10.0, angle_deg=45.0)
    pattern = FieldLawnmowerSearchPattern(geometry, 5.0)
    near_u_max = geometry.field_uv_to_ned(24.0, -8.0)

    assert pattern.start_from_x_max_is_nearest(near_u_max.x, near_u_max.y)


def test_field_lawnmower_velocity_is_returned_in_ned():
    geometry = _geometry(50.0, 10.0, angle_deg=45.0)
    pattern = FieldLawnmowerSearchPattern(geometry, 5.0)
    position = geometry.field_uv_to_ned(0.0, -5.0)

    index, vx, vy = pattern.next_velocity_from_start(position.x, position.y, 1, 2.0, 0.5, False)
    vu, vv = geometry.vector_ned_to_field_uv(vx, vy)

    assert index == 1
    assert _approx(vu, 2.0, abs_tol=1e-9)
    assert _approx(vv, 0.0, abs_tol=1e-9)


def test_field_point_and_vector_roundtrip():
    geometry = _geometry(100.0, 30.0, angle_deg=33.0)
    point = geometry.field_uv_to_ned(12.0, -4.0)
    u, v = geometry.ned_to_field_uv(point)
    vx, vy = geometry.vector_field_uv_to_ned(2.0, 0.0)
    vu, vv = geometry.vector_ned_to_field_uv(vx, vy)

    assert _approx(u, 12.0, abs_tol=1e-9)
    assert _approx(v, -4.0, abs_tol=1e-9)
    assert _approx(vu, 2.0, abs_tol=1e-9)
    assert _approx(vv, 0.0, abs_tol=1e-9)


if __name__ == "__main__":
    test_lawnmower_waypoints_alternate_direction()
    test_lawnmower_advances_after_passing_lane_endpoint()
    test_lawnmower_advances_at_lane_endpoint_with_cross_track_error()
    test_lawnmower_does_not_return_along_completed_lane()
    test_lawnmower_horizontal_lane_has_no_lateral_velocity()
    test_lawnmower_can_start_from_nearest_x_max_side()
    test_nearest_start_avoids_crossing_to_far_lane_start()
    test_axis_aligned_field_lawnmower_matches_legacy_waypoints()
    test_rotated_field_lanes_are_parallel_to_long_axis()
    test_field_lawnmower_endpoints_stay_inside_uv_bounds_for_sizes()
    test_field_lawnmower_nearest_start_uses_field_local_coordinates()
    test_field_lawnmower_velocity_is_returned_in_ned()
    test_field_point_and_vector_roundtrip()
