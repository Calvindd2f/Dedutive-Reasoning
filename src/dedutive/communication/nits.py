from __future__ import annotations


class NitsStrategy:
    name = "NITS"

    def adapter_text(self) -> str:
        return (
            "Produce a handoff brief with Nature, Intention, Time, and Special instructions. "
            "Use it for communication, not diagnosis."
        )
