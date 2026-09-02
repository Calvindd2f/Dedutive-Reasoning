from __future__ import annotations


class FordecStrategy:
    name = "FORDEC"

    def adapter_text(self) -> str:
        return (
            "Use Facts, Options, Risks and benefits, Decision, Execution, Check. "
            "Do not jump directly from facts to action. "
            "Explicitly compare at least two options before choosing one."
        )
