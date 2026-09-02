# Dedutive

A configurable multi-agent IT troubleshooting orchestration architecture.

## What Dedutive is

Deductive orchestrates IT incident troubleshooting through five independently configurable strategy dimensions: 
reasoning, governance, decision, communication, and learning, composed by a central orchestrator around a
provider-independent troubleshooting trajectory.   
A deterministic evaluation subsystem (the original benchmark) lets you compare how different strategy
configurations perform against the same fixed incident scenarios.

## Why this architecture exists

Real IT troubleshooting draws on several distinct reasoning disciplines at
once: 

- how to diagnose (Kepner-Tregoe, Recognition-Primed Decision)
- how much participation a decision needs (Vroom-Yetton-Jago)
- how to structure a risky action (FORDEC)
- how to hand off to another responder (NITS)
- how deeply to learn from the incident afterward (single- vs double-loop learning)

Treating these as one monolithic prompt collapses all of that structure into
generic troubleshooting mush. Dedutive keeps each dimension as a small,
swappable strategy so the same incident can be run under different
configurations and compared.

## Orchestration lifecycle

```text
incident
  -> framing
  -> hypothesis generation
  -> evidence selection
  -> evidence observation
  -> hypothesis update
  -> decision
  -> action
  -> verification
  -> learning
  -> communication/handoff
```

A `TroubleshootingSession` (`src/dedutive/orchestrator/session.py`) pairs a
`ScenarioCase` with one strategy per dimension and produces a `Trajectory`
(`src/dedutive/orchestrator/trajectory.py`) recording each step. The
trajectory is a plain structured record, independent of any specific LLM
provider.

## Configurable strategy dimensions

| Dimension | Interface | Built-in strategies |
|---|---|---|
| Reasoning | `dedutive.reasoning.protocol.ReasoningStrategy` | Kepner-Tregoe, Recognition-Primed Decision, hybrid |
| Governance | `dedutive.governance.protocol.GovernanceStrategy` | Vroom-Yetton-Jago |
| Decision | `dedutive.decision.protocol.DecisionStrategy` | FORDEC |
| Communication | `dedutive.communication.protocol.CommunicationStrategy` | NITS |
| Learning | `dedutive.learning.protocol.LearningStrategy` | single-loop, double-loop |

Each is a small `Protocol` implementation, not an agent. The orchestrator
depends only on the protocol, never a concrete class
(see `src/dedutive/orchestrator/config.py`'s `build_*_strategy` functions).

Configuration is plain YAML, one file per experiment:

```yaml
reasoning:
  strategy: kepner_tregoe
governance:
  strategy: vroom_yetton
decision:
  strategy: fordec
communication:
  strategy: nits
learning:
  strategy: double_loop
```

See `configs/experiments/` for ready-made configurations.

## How evaluation works

The evaluation subsystem (`src/dedutive/evaluation/`) is deterministic and
runs fully offline - no LLM judge required. It scores a run's structured
response contract against a hidden answer key on: schema validity, valid
tool use, no hallucinated tool observations, gold evidence coverage, gold
action coverage, unsafe action avoidance, verification completeness, NITS
shape, and framework fidelity (`src/dedutive/evaluation/scoring.py`). It also
derives named trajectory metrics - root-cause accuracy, evidence relevance,
hypothesis quality, unnecessary investigation, unsafe action rate, decision
quality, escalation appropriateness, verification success, communication
completeness, and systemic learning - from the same deterministic score
(`src/dedutive/evaluation/metrics.py`).

## How experiments compare configurations

`dedutive experiment compare --experiments configs/experiments/baseline_a.yaml,configs/experiments/baseline_b.yaml`
runs the same scenario set under each experiment configuration and reports
mean score per configuration, so you can ask "does Kepner-Tregoe actually
beat Recognition-Primed Decision on this scenario set?" rather than assuming
it.

## Quick start: run a troubleshooting session

```powershell
uv sync
uv run dedutive scenario validate
uv run dedutive inspect configs/experiments/baseline_a.yaml --limit 1
```

Copy `.env.example` to `.env` and set `OPENAI_COMPATIBLE_BASE_URL`,
`OPENAI_COMPATIBLE_API_KEY`, `OPENAI_COMPATIBLE_MODEL`, then:

```powershell
uv run dedutive run --experiment configs/experiments/baseline_a.yaml --limit 1
```

## Quick start: run an evaluation

```powershell
uv run dedutive evaluate --run runs/<your-run-file>.jsonl
```

## Runtime vs. evaluation

The orchestrator (`src/dedutive/orchestrator/`) is the runtime: given a
scenario and a strategy configuration, it produces a trajectory. The
evaluation subsystem (`src/dedutive/evaluation/`) is a downstream consumer
of runtime output - it never influences the orchestrator's behavior. This
keeps the benchmark an evaluation capability of Dedutive, not the other way
around.

## Data layout

- `data/strategies/reasoning.json` - reasoning/decision/communication adapter
  text, governance mode descriptions, and stage-arm definitions.
- `data/strategies/stage_policies.json` - static staged assignment policies
  (bandit-ready logging inputs).
- `data/tools/catalog.json` - the deterministic tool surface.
- `data/scenarios/seed.jsonl` / `data/answers/seed_answer_key.jsonl` - the
  30-case seed benchmark (visible scenario / hidden answer key).
- `runs/`, `reports/` - run and score output locations.

## Authoring and generation

```powershell
uv run dedutive scenario new IDAUTH-011 "Example incident"
uv run dedutive scenario generate --source data/sources/issues_resolutions.example.jsonl --output-scenarios data/scenarios/generated.jsonl --output-answers data/answers/generated_answer_key.jsonl --variants-per-source 3
uv run dedutive scenario validate --scenarios data/scenarios/generated.jsonl --answers data/answers/generated_answer_key.jsonl
```

## Legacy CLI

The original benchmark-only CLI remains available for backwards
compatibility as `rca-bench` (`deductive_rca_bench` package), which
re-exports everything from `dedutive`. New work should use the `dedutive`
CLI and package.

## Background

The stage-assignment policy layer and bandit-ready logging design now live
under `dedutive.reasoning` and `dedutive.evaluation`; see
`docs/stage_policies.md` and `docs/schema.md` for the design rationale.
