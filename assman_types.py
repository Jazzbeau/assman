from typing import Mapping, Sequence, TypeAlias

JSONType: TypeAlias = (
    str | int | float | bool | None | Mapping[str, "JSONType"] | Sequence["JSONType"]
)
