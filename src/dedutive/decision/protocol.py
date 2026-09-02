from __future__ import annotations

from typing import Protocol


class DecisionStrategy(Protocol):
    name: str

    def adapter_text(self) -> str:
        ...
