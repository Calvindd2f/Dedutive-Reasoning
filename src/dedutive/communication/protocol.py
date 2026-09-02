from __future__ import annotations

from typing import Protocol


class CommunicationStrategy(Protocol):
    name: str

    def adapter_text(self) -> str:
        ...
