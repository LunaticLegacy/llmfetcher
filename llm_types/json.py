"""JSON value aliases shared by every provider-neutral payload.

Kept dependency-free so any other module in the package can import them
without pulling in dataclass models.
"""

from __future__ import annotations

from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
JsonArray: TypeAlias = list[JsonValue]

__all__ = ["JsonArray", "JsonObject", "JsonScalar", "JsonValue"]
