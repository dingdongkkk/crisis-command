"""Shared contract primitives (decision record 0001).

Every model forbids unknown fields. Named ``PydanticCustomError`` types carry the
machine error codes used by the contract fixtures, so tests and the API can report
``UTC_Z_REQUIRED`` rather than a generic Pydantic message.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic_core import PydanticCustomError

SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_MAJOR = "1"


class Contract(BaseModel):
    """Base for every canonical model: closed, no coercion of unknown fields."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --- Integers ---------------------------------------------------------------------------


def _require_int(code: str, message: str) -> Any:
    def check(value: Any) -> Any:
        if isinstance(value, bool) or not isinstance(value, int):
            raise PydanticCustomError(code, message)
        return value

    return check


Seconds = Annotated[
    int,
    BeforeValidator(_require_int("INTEGER_SECONDS_REQUIRED", "durations are integer seconds")),
    Field(ge=0),
]
"""Non-negative integer seconds (durations, ETAs, simulation time)."""

Metres = Annotated[
    int,
    BeforeValidator(_require_int("INTEGER_METRES_REQUIRED", "distances are integer metres")),
    Field(ge=0),
]
Persons = Annotated[
    int,
    BeforeValidator(_require_int("INTEGER_COUNT_REQUIRED", "counts are integers")),
    Field(ge=0),
]
Beds = Persons
NonNegativeInt = Persons
Sequence = Annotated[
    int,
    BeforeValidator(
        _require_int("POSITIVE_SEQUENCE_REQUIRED", "sequence is an integer starting at 1")
    ),
    AfterValidator(lambda v: _positive(v, "POSITIVE_SEQUENCE_REQUIRED")),
]
Version = Annotated[
    int,
    BeforeValidator(_require_int("POSITIVE_VERSION_REQUIRED", "versions are integers")),
    AfterValidator(lambda v: _positive(v, "POSITIVE_VERSION_REQUIRED")),
]


def _positive(value: int, code: str) -> int:
    if value < 1:
        raise PydanticCustomError(code, "must be at least 1")
    return value


# --- Time -------------------------------------------------------------------------------

_UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def _utc_z(value: Any) -> Any:
    if not isinstance(value, str) or not _UTC_Z.fullmatch(value):
        raise PydanticCustomError(
            "UTC_Z_REQUIRED", "timestamps are RFC 3339 UTC with millisecond precision and Z"
        )
    return value


UtcTimestamp = Annotated[
    str,
    BeforeValidator(_utc_z),
    Field(
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
        examples=["2026-09-30T09:10:00.000Z"],
    ),
]

# --- Schema version ---------------------------------------------------------------------


def _schema_version(value: Any) -> Any:
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+", value):
        raise PydanticCustomError("SCHEMA_VERSION_FORMAT", "schema_version is MAJOR.MINOR")
    if value.split(".")[0] != SUPPORTED_SCHEMA_MAJOR:
        raise PydanticCustomError("UNKNOWN_SCHEMA_MAJOR", "unsupported schema major version")
    return value


SchemaVersion = Annotated[str, BeforeValidator(_schema_version), Field(pattern=r"^1\.\d+$")]

# --- Identifiers ------------------------------------------------------------------------

Id = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_:.\-]+$")]
Uuid = Annotated[
    str,
    Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
]
Code = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]*$")]

# --- Geometry ---------------------------------------------------------------------------


def _coordinate(limit: float, name: str) -> Any:
    def check(value: Any) -> Any:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise PydanticCustomError("COORDINATE_NUMBER_REQUIRED", "coordinates are numbers")
        if not -limit <= value <= limit:
            raise PydanticCustomError(
                "COORDINATE_OUT_OF_RANGE",
                "{name} {value} outside [-{limit}, {limit}]",
                {"name": name, "value": value, "limit": limit},
            )
        if round(float(value), 6) != float(value):
            raise PydanticCustomError("COORDINATE_PRECISION", "at most six decimal places")
        return float(value)

    return check


Longitude = Annotated[float, BeforeValidator(_coordinate(180, "longitude"))]
Latitude = Annotated[float, BeforeValidator(_coordinate(90, "latitude"))]
Position = tuple[Longitude, Latitude]
"""GeoJSON position, always ``[longitude, latitude]``."""


class Point(Contract):
    type: Literal["Point"]
    coordinates: Position

    @model_validator(mode="before")
    @classmethod
    def _geojson_only(cls, data: Any) -> Any:
        if not isinstance(data, dict) or set(data) != {"type", "coordinates"}:
            raise PydanticCustomError(
                "GEOJSON_POINT_REQUIRED",
                "location must be a GeoJSON Point {type, coordinates:[lon, lat]}",
            )
        return data


def _ring(ring: list[Position]) -> list[Position]:
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise PydanticCustomError(
            "POLYGON_RING_INVALID", "ring must have ≥ 4 positions and be closed"
        )
    return ring


LinearRing = Annotated[list[Position], AfterValidator(_ring)]


class Polygon(Contract):
    type: Literal["Polygon"]
    coordinates: Annotated[list[LinearRing], Field(min_length=1)]


class LineString(Contract):
    type: Literal["LineString"]
    coordinates: Annotated[list[Position], Field(min_length=2)]


# --- Reasons and problems ---------------------------------------------------------------

ReasonParam = str | int | bool | list[str] | None


class ReasonFact(Contract):
    """Typed evidence for explanations; templates and models may only restate these."""

    code: Code
    params: dict[str, ReasonParam] = Field(default_factory=dict)


class ProblemFieldError(Contract):
    pointer: str
    message: str


class Problem(Contract):
    """RFC 9457 problem details with a stable machine ``code`` (0001)."""

    type: str
    title: str
    status: Annotated[int, Field(ge=400, le=599)]
    code: Code
    detail: str | None = None
    instance: str | None = None
    current: dict[str, Any] | None = None
    errors: list[ProblemFieldError] | None = None
    missing_flag_ids: list[Id] | None = None
    conflicts: list[dict[str, Any]] | None = None
    override_id: Id | None = None
    reason: Code | None = None


DEMO_BOUNDS = (77.45, 12.80, 77.80, 13.15)
"""``[min_lon, min_lat, max_lon, max_lat]`` enforced on fixtures only, not the schema."""


def in_demo_bounds(point: Point) -> bool:
    lon, lat = point.coordinates
    min_lon, min_lat, max_lon, max_lat = DEMO_BOUNDS
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
