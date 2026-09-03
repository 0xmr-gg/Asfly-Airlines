from __future__ import annotations

"""Drone telemetry and command payload models.

These dataclasses are the boundary between mission logic and MAVLink bridge
JSON. Keeping the model here makes it easier to replace JSON/String topics with
custom ROS messages later.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DroneState:
    connected: bool = False
    armed: bool = False
    mode: str = "UNKNOWN"
    system_id: int | None = None
    component_id: int | None = None
    last_heartbeat_s: float | None = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "DroneState":
        data = json.loads(text)
        return cls(
            connected=bool(data.get("connected", False)),
            armed=bool(data.get("armed", False)),
            mode=str(data.get("mode", "UNKNOWN")),
            system_id=int(data["system_id"]) if data.get("system_id") is not None else None,
            component_id=int(data["component_id"]) if data.get("component_id") is not None else None,
            last_heartbeat_s=float(data["last_heartbeat_s"]) if data.get("last_heartbeat_s") is not None else None,
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class LocalPosition:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    frame: str = "NED"
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LocalPosition":
        data: dict[str, Any] = json.loads(text)
        return cls(
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z=float(data.get("z", 0.0)),
            vx=float(data.get("vx", 0.0)),
            vy=float(data.get("vy", 0.0)),
            vz=float(data.get("vz", 0.0)),
            frame=str(data.get("frame", "NED")),
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class Altitude:
    relative_m: float = 0.0
    amsl_m: float | None = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "Altitude":
        data = json.loads(text)
        return cls(
            relative_m=float(data.get("relative_m", 0.0)),
            amsl_m=float(data["amsl_m"]) if data.get("amsl_m") is not None else None,
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class GlobalPosition:
    lat_deg: float | None = None
    lon_deg: float | None = None
    relative_m: float | None = None
    amsl_m: float | None = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "GlobalPosition":
        data = json.loads(text)
        return cls(
            lat_deg=float(data["lat_deg"]) if data.get("lat_deg") is not None else None,
            lon_deg=float(data["lon_deg"]) if data.get("lon_deg") is not None else None,
            relative_m=float(data["relative_m"]) if data.get("relative_m") is not None else None,
            amsl_m=float(data["amsl_m"]) if data.get("amsl_m") is not None else None,
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class GpsStatus:
    fix_type: int | None = None
    satellites_visible: int | None = None
    eph: float | None = None
    epv: float | None = None
    hdop: float | None = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "GpsStatus":
        data = json.loads(text)
        return cls(
            fix_type=int(data["fix_type"]) if data.get("fix_type") is not None else None,
            satellites_visible=int(data["satellites_visible"]) if data.get("satellites_visible") is not None else None,
            eph=float(data["eph"]) if data.get("eph") is not None else None,
            epv=float(data["epv"]) if data.get("epv") is not None else None,
            hdop=float(data["hdop"]) if data.get("hdop") is not None else None,
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class GlobalOrigin:
    lat_deg: float | None = None
    lon_deg: float | None = None
    alt_m: float | None = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "GlobalOrigin":
        data = json.loads(text)
        return cls(
            lat_deg=float(data["lat_deg"]) if data.get("lat_deg") is not None else None,
            lon_deg=float(data["lon_deg"]) if data.get("lon_deg") is not None else None,
            alt_m=float(data["alt_m"]) if data.get("alt_m") is not None else None,
            timestamp=float(data.get("timestamp", time.time())),
        )


@dataclass
class HomePosition:
    lat_deg: float | None = None
    lon_deg: float | None = None
    alt_m: float | None = None
    x: float | None = None
    y: float | None = None
    z: float | None = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "HomePosition":
        data = json.loads(text)
        return cls(
            lat_deg=float(data["lat_deg"]) if data.get("lat_deg") is not None else None,
            lon_deg=float(data["lon_deg"]) if data.get("lon_deg") is not None else None,
            alt_m=float(data["alt_m"]) if data.get("alt_m") is not None else None,
            x=float(data["x"]) if data.get("x") is not None else None,
            y=float(data["y"]) if data.get("y") is not None else None,
            z=float(data["z"]) if data.get("z") is not None else None,
            timestamp=float(data.get("timestamp", time.time())),
        )


def command_json(command: str, **params: Any) -> str:
    payload = {"command": command, "timestamp": time.time()}
    payload.update(params)
    return json.dumps(payload, separators=(",", ":"))
