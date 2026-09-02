# Refactor Dedutive Reasoning from RCA Benchmark into Troubleshooting Orchestrator

We need to restructure this repository conceptually and architecturally.

The repository is currently implemented and described primarily as a "Deductive RCA Bench" / benchmark harness. That framing is now too narrow.

The intended project is:

**Dedutive Reasoning: a configurable multi-agent IT troubleshooting orchestration architecture.**

The benchmark/evaluation functionality should remain, but become a first-class subsystem of the broader architecture rather than defining the entire project.

## Core conceptual model

The target architecture is:

```text
                    IT Troubleshooting
                        Orchestrator
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          Reasoning       Governance       Decision
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                        Verification
                              │
                              ▼
                          Learning
                              │
                              ▼
                       Communication
```

The architecture should support configurable strategies across these dimensions:

```text
scenario
× reasoning_strategy
× governance_strategy
× decision_strategy
× communication_strategy
× learning_strategy
```

The same incident should therefore be executable under different reasoning configurations and produce a comparable troubleshooting trajectory.

## Existing implementation

Inspect the entire repository before making changes.

The current implementation contains useful functionality including:

* scenario definitions
* hidden answer keys
* deterministic tool simulation
* framework adapters
* staged policies
* provider abstraction
* prompt generation
* inference execution
* scoring
* report generation
* scenario generation from documented issues
* contextual-bandit-ready stage logs

Do NOT discard this functionality simply because the project framing is changing.

Instead, identify which existing components belong under:

1. orchestration/runtime
2. reasoning strategies
3. governance strategies
4. decision/action strategies
5. communication strategies
6. learning strategies
7. tool/environment interfaces
8. evaluation/benchmarking
9. scenario generation
10. model providers

## Target domain model

Introduce a clear domain model around a troubleshooting session.

Conceptually:

```text
TroubleshootingSession
├── Scenario
├── ReasoningStrategy
├── GovernanceStrategy
├── DecisionStrategy
├── CommunicationStrategy
├── LearningStrategy
├── ToolEnvironment
└── Trajectory
```

A session should produce a structured troubleshooting trajectory.

Conceptually:

```text
incident
→ framing
→ hypothesis generation
→ evidence selection
→ evidence observation
→ hypothesis update
→ decision
→ action
→ verification
→ learning
→ communication/handoff
```

The trajectory must be representable independently of a specific LLM provider.

## Strategy architecture

Create explicit interfaces/protocols for strategy types rather than hard-coding framework logic into the orchestrator.

Initially support the concepts already represented in the repository:

### Reasoning

* Kepner-Tregoe
* Recognition-Primed Decision
* hybrid strategies where appropriate

### Governance

* Vroom-Yetton-Jago

### Decision / action

* FORDEC

### Communication

* NITS

### Learning

* single-loop learning
* double-loop learning

Do not create unnecessary abstraction layers.

Prefer small Python protocols/classes and composition.

The orchestrator should depend on interfaces, not concrete framework implementations.

## Important distinction

Do NOT implement every framework as an enormous independent agent.

The frameworks are strategy policies that influence how the orchestrator performs a stage or transition.

Avoid:

```text
AgentFactory
AgentManager
AgentStrategyFactory
FrameworkFactory
FrameworkAgentFactory
```

unless there is a demonstrated technical need.

Prefer composition:

```text
Orchestrator
    receives
ReasoningStrategy
GovernanceStrategy
DecisionStrategy
...
```

## Evaluation architecture

The existing benchmark functionality should become the evaluation subsystem.

The evaluation system should be capable of comparing:

```text
scenario A
    +
configuration X
    →
trajectory X

scenario A
    +
configuration Y
    →
trajectory Y
```

Evaluation should measure more than final RCA correctness where possible.

Define metrics around:

* root-cause accuracy
* evidence relevance
* hypothesis quality
* unnecessary investigation
* unsafe action rate
* decision quality
* escalation appropriateness
* verification success
* communication/handoff completeness
* systemic/root-cause learning

Keep deterministic scoring where possible.

Do not replace deterministic evaluation with an LLM judge merely because it is easier.

## Configuration

Introduce a clean configuration representation.

For example:

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

The architecture should make it easy to run controlled experiments by changing only this configuration.

## CLI

The current CLI is benchmark-oriented.

Refactor it toward a project-level CLI such as:

```text
dedutive run
dedutive evaluate
dedutive scenario
dedutive frameworks
dedutive experiment
dedutive inspect
```

Preserve backwards compatibility where practical, but the primary interface should no longer be named `rca-bench`.

## Repository structure

Move toward a structure broadly resembling:

```text
src/
  dedutive/
    orchestrator/
    reasoning/
    governance/
    decision/
    communication/
    learning/
    tools/
    evaluation/
    scenarios/
    providers/

configs/
  reasoning/
  governance/
  decision/
  communication/
  learning/
  experiments/

data/
  scenarios/
  answers/
  tools/
  sources/

experiments/
docs/
tests/
```

Do not blindly follow this tree if inspection of the existing implementation suggests a better structure. Preserve simplicity.

## README

Rewrite the README around the architecture rather than the benchmark.

The README should explain:

1. what Dedutive is
2. why the architecture exists
3. the orchestration lifecycle
4. the configurable strategy dimensions
5. how evaluation works
6. how experiments compare configurations
7. how to run a simple troubleshooting session
8. how to run an evaluation
9. the relationship between runtime and evaluation

The README should NOT present the repository primarily as a benchmark harness.

The benchmark is an evaluation capability of Dedutive.

## Migration requirements

Before modifying code:

1. inspect all source files
2. inspect all tests
3. inspect the existing data schemas
4. inspect PLAN.md and info_0.md through info_3.md
5. identify existing functionality that must be preserved
6. produce a short migration plan

Then implement the refactor incrementally.

Do not rewrite functioning code merely for naming consistency.

Do not delete existing functionality unless it is genuinely obsolete.

Maintain or improve test coverage.

After restructuring:

* run the full test suite
* run validation against existing datasets
* run a sample inference/evaluation
* verify existing scenario generation still works
* verify deterministic scoring still works
* verify provider abstraction still works

Finally, update documentation and examples to reflect the new architecture.

## Architectural success criterion

The finished repository should make this statement true:

> Dedutive is a configurable IT troubleshooting orchestration architecture whose reasoning, governance, decision, communication, and learning strategies can be varied independently and evaluated against controlled incident scenarios.

The benchmark should be an implementation detail of that larger architecture, not the project's identity.
