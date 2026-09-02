# Stage Assignment Policies

The five-stage pipeline (`framing -> hypothesis -> check_selection -> decision -> review`)
described here is the internal machinery of `dedutive`'s `ReasoningStrategy`
implementations (see `src/dedutive/reasoning/`). Governance, decision, communication,
and learning are separate, independently configurable strategy dimensions — see
`configs/` and `README.md`'s "Configurable strategy dimensions" section.

The benchmark supports a staged assignment-policy layer that assigns one strategy arm per stage.

V1 does not implement online learning. It runs static policies and records enough structured data for contextual bandit experiments later.

## Stages

- `framing`
- `hypothesis`
- `check_selection`
- `decision`
- `review`

## Baselines

`data/strategies/stage_policies.json` defines four starting policies:

- `baseline_a`: `grade -> kt -> kt -> fordec -> single_loop`
- `baseline_b`: `safe -> rpd -> shor -> fordec -> nits`
- `baseline_c`: `3p -> kt -> shor -> care -> double_loop`
- `generic_baseline`: `generic -> generic -> generic -> generic -> generic`

## Bandit-Ready Logs

When scoring a policy run with `--bandit-log`, the scorer emits one JSONL row per stage with:

- case and scenario IDs
- policy ID
- contextual assignment features
- stage name
- chosen arm
- candidate arms
- projected stage reward
- final scenario score

This keeps the reward signal close to each stage while preserving the final scenario score for later analysis.
