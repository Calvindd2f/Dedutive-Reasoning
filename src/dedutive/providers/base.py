from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class GenerationResult:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Provider(Protocol):
    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> GenerationResult:
        ...
