from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EARTH_RADIUS_M = 6371000.0
DUPLICATE_POINT_THRESHOLD_M = 0.1
MIN_FIELD_AREA_M2 = 1.0


class FieldConfigError(ValueError):
    """Raised when mission field configuration or geometry is invalid."""


@dataclass(frozen=True)
class WGS84Corner:
    lat: float
    lon: float


@dataclass(frozen=True)
class LocalPoint:
    x: float
    y: float


@dataclass(frozen=True)
class FieldGeometry:
    corners_wgs84: tuple[WGS84Corner, WGS84Corner, WGS84Corner, WGS84Corner]
    corners_ned: tuple[LocalPoint, LocalPoint, LocalPoint, LocalPoint]
    center: LocalPoint
    u_axis: tuple[float, float]
    v_axis: tuple[float, float]
    long_length_m: float
    short_length_m: float
    edge_lengths_m: tuple[float, float, float, float]
    area_m2: float
    u_min: float
    u_max: float
    v_min: float
    v_max: float

    def ned_to_field_uv(self, point: LocalPoint | tuple[float, float]) -> tuple[float, float]:
        x, y = _point_xy(point)
        dx = x - self.center.x
        dy = y - self.center.y
        return dx * self.u_axis[0] + dy * self.u_axis[1], dx * self.v_axis[0] + dy * self.v_axis[1]

    def field_uv_to_ned(self, u: float, v: float) -> LocalPoint:
        return LocalPoint(
            self.center.x + u * self.u_axis[0] + v * self.v_axis[0],
            self.center.y + u * self.u_axis[1] + v * self.v_axis[1],
        )

    def vector_ned_to_field_uv(self, vx: float, vy: float) -> tuple[float, float]:
        return vx * self.u_axis[0] + vy * self.u_axis[1], vx * self.v_axis[0] + vy * self.v_axis[1]

    def vector_field_uv_to_ned(self, vu: float, vv: float) -> tuple[float, float]:
        return vu * self.u_axis[0] + vv * self.v_axis[0], vu * self.u_axis[1] + vv * self.v_axis[1]


def load_mission_field(path: str | Path) -> tuple[WGS84Corner, WGS84Corner, WGS84Corner, WGS84Corner]:
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise FieldConfigError(f"mission_field.json cannot be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FieldConfigError(f"mission_field.json is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise FieldConfigError("mission_field.json root must be an object")
    if data.get("version") != 1:
        raise FieldConfigError("mission_field.json version must be 1")
    if data.get("coordinate_system") != "WGS84":
        raise FieldConfigError('mission_field.json coordinate_system must be "WGS84"')
    corners = data.get("corners")
    if not isinstance(corners, list) or len(corners) != 4:
        raise FieldConfigError("mission_field.json must contain exactly 4 corners")

    parsed: list[WGS84Corner] = []
    for index, corner in enumerate(corners):
        if not isinstance(corner, dict):
            raise FieldConfigError(f"corner {index} must be an object")
        if "lat" not in corner or "lon" not in corner:
            raise FieldConfigError(f"corner {index} must contain lat and lon")
        try:
            lat = float(corner["lat"])
            lon = float(corner["lon"])
        except (TypeError, ValueError) as exc:
            raise FieldConfigError(f"corner {index} lat/lon must be numeric") from exc
        if not -90.0 <= lat <= 90.0:
            raise FieldConfigError(f"corner {index} lat must be in [-90, 90]")
        if not -180.0 <= lon <= 180.0:
            raise FieldConfigError(f"corner {index} lon must be in [-180, 180]")
        parsed.append(WGS84Corner(lat=lat, lon=lon))
    return parsed[0], parsed[1], parsed[2], parsed[3]


def wgs84_to_ned_xy(origin_lat_deg: float, origin_lon_deg: float, lat_deg: float, lon_deg: float) -> tuple[float, float]:
    origin_lat = math.radians(float(origin_lat_deg))
    lat = math.radians(float(lat_deg))
    d_lat = lat - origin_lat
    d_lon = math.radians(float(lon_deg) - float(origin_lon_deg))
    mean_lat = 0.5 * (origin_lat + lat)
    north_m = d_lat * EARTH_RADIUS_M
    east_m = d_lon * EARTH_RADIUS_M * math.cos(mean_lat)
    return north_m, east_m


def build_field_geometry(corners_wgs84: Iterable[WGS84Corner], global_origin: Any) -> FieldGeometry:
    origin_lat, origin_lon = _origin_lat_lon(global_origin)
    corners = tuple(corners_wgs84)
    if len(corners) != 4:
        raise FieldConfigError("field geometry requires exactly 4 WGS84 corners")
    projected = tuple(LocalPoint(*wgs84_to_ned_xy(origin_lat, origin_lon, c.lat, c.lon)) for c in corners)
    _reject_duplicate_points(projected)
    ordered_pairs = _order_pairs_around_centroid(tuple(zip(projected, corners)))
    ordered = tuple(point for point, _corner in ordered_pairs)
    ordered_corners = tuple(corner for _point, corner in ordered_pairs)
    if _has_self_intersection(ordered):
        raise FieldConfigError("field corners form a self-intersecting quadrilateral")
    signed_area = _signed_area(ordered)
    area = abs(signed_area)
    if area <= MIN_FIELD_AREA_M2:
        raise FieldConfigError("field area is too small or degenerate")
    if not _is_convex(ordered):
        raise FieldConfigError("field corners must form a convex quadrilateral")
    if signed_area < 0.0:
        ordered = tuple(reversed(ordered))  # keep a stable counter-clockwise order
        ordered_corners = tuple(reversed(ordered_corners))

    center = LocalPoint(sum(p.x for p in ordered) / 4.0, sum(p.y for p in ordered) / 4.0)
    edge_lengths = tuple(_distance(ordered[i], ordered[(i + 1) % 4]) for i in range(4))
    longest_index = max(range(4), key=lambda i: edge_lengths[i])
    p0 = ordered[longest_index]
    p1 = ordered[(longest_index + 1) % 4]
    dx = p1.x - p0.x
    dy = p1.y - p0.y
    length = math.hypot(dx, dy)
    if length <= 0.0:
        raise FieldConfigError("field long axis is degenerate")
    u_axis = (dx / length, dy / length)
    v_axis = (-u_axis[1], u_axis[0])
    uv = [((p.x - center.x) * u_axis[0] + (p.y - center.y) * u_axis[1], (p.x - center.x) * v_axis[0] + (p.y - center.y) * v_axis[1]) for p in ordered]
    u_values = [p[0] for p in uv]
    v_values = [p[1] for p in uv]
    sorted_edges = sorted(edge_lengths)

    return FieldGeometry(
        corners_wgs84=ordered_corners, corners_ned=ordered, center=center, u_axis=u_axis, v_axis=v_axis,
        long_length_m=(sorted_edges[2] + sorted_edges[3]) / 2.0,
        short_length_m=(sorted_edges[0] + sorted_edges[1]) / 2.0,
        edge_lengths_m=edge_lengths, area_m2=area,
        u_min=min(u_values), u_max=max(u_values), v_min=min(v_values), v_max=max(v_values),
    )


def _origin_lat_lon(global_origin: Any) -> tuple[float, float]:
    if isinstance(global_origin, dict):
        lat = global_origin.get("lat_deg")
        lon = global_origin.get("lon_deg")
    else:
        lat = getattr(global_origin, "lat_deg", None)
        lon = getattr(global_origin, "lon_deg", None)
    if lat is None or lon is None:
        raise FieldConfigError("/drone/global_origin must contain lat_deg and lon_deg")
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError) as exc:
        raise FieldConfigError("/drone/global_origin lat_deg/lon_deg must be numeric") from exc
    if not -90.0 <= lat_f <= 90.0 or not -180.0 <= lon_f <= 180.0:
        raise FieldConfigError("/drone/global_origin lat_deg/lon_deg out of range")
    return lat_f, lon_f


def _point_xy(point: LocalPoint | tuple[float, float]) -> tuple[float, float]:
    if isinstance(point, LocalPoint):
        return point.x, point.y
    return float(point[0]), float(point[1])


def _reject_duplicate_points(points: tuple[LocalPoint, ...]) -> None:
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if _distance(points[i], points[j]) < DUPLICATE_POINT_THRESHOLD_M:
                raise FieldConfigError("field corners contain duplicate/near-duplicate points")


def _order_pairs_around_centroid(pairs: tuple[tuple[LocalPoint, WGS84Corner], ...]) -> tuple[tuple[LocalPoint, WGS84Corner], ...]:
    cx = sum(p.x for p, _corner in pairs) / len(pairs)
    cy = sum(p.y for p, _corner in pairs) / len(pairs)
    return tuple(sorted(pairs, key=lambda pair: math.atan2(pair[0].y - cy, pair[0].x - cx)))


def _distance(a: LocalPoint, b: LocalPoint) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _signed_area(points: tuple[LocalPoint, ...]) -> float:
    total = 0.0
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        total += p.x * q.y - q.x * p.y
    return 0.5 * total


def _is_convex(points: tuple[LocalPoint, ...]) -> bool:
    signs: list[float] = []
    for i in range(len(points)):
        a = points[i]
        b = points[(i + 1) % len(points)]
        c = points[(i + 2) % len(points)]
        cross = (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x)
        if abs(cross) <= 1e-9:
            return False
        signs.append(cross)
    return all(s > 0.0 for s in signs) or all(s < 0.0 for s in signs)


def _has_self_intersection(points: tuple[LocalPoint, ...]) -> bool:
    return _segments_intersect(points[0], points[1], points[2], points[3]) or _segments_intersect(points[1], points[2], points[3], points[0])


def _segments_intersect(a: LocalPoint, b: LocalPoint, c: LocalPoint, d: LocalPoint) -> bool:
    def orient(p: LocalPoint, q: LocalPoint, r: LocalPoint) -> float:
        return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)

    return orient(a, b, c) * orient(a, b, d) < 0.0 and orient(c, d, a) * orient(c, d, b) < 0.0
