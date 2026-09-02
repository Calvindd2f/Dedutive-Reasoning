# Dataset Schema

The benchmark separates visible scenario cards from hidden answer keys.

Visible cases live in `data/scenarios/seed.jsonl`. They include the prompt, taxonomy labels, available deterministic tools, and scripted observations used by the local simulator.

Hidden answer keys live in `data/answers/seed_answer_key.jsonl`. They include root causes, acceptable remediations, gold evidence, gold actions, unsafe actions, and verification requirements.

Model outputs should follow the visible response contract rendered by `dedutive inspect`. The contract captures structured reasoning artifacts such as hypotheses, next best tests, decision, execution plan, verification steps, NITS brief, and post-incident learning.

## Stage Assignment Policies

The v1 assignment-policy direction: use fixed staged policies first, then collect clean logs for future contextual bandits.

Policies live in `data/strategies/stage_policies.json` and assign one arm to each stage:

- `framing`
- `hypothesis`
- `check_selection`
- `decision`
- `review`

The stage arms are defined in `data/strategies/reasoning.json` under `stage_arms`. Current arms include `safe`, `grade`, `3p`, `kt`, `rpd`, `shor`, `fordec`, `care`, `5d`, `nits`, `single_loop`, `double_loop`, and `generic`.

Policy runs can export bandit-ready JSONL rows with `dedutive evaluate --run <path> --bandit-log <path>`. Each row contains scenario context, selected arm, candidate arms, projected stage reward, final score, and optional stage output summary.

## Documented Issue Source Schema

`data/sources/issues_resolutions.example.jsonl` shows the input format for `dedutive scenario generate`.

Required fields:

- `source_id`
- `title`
- `task_family`
- `issue_summary`
- `symptoms`
- `documented_root_cause`
- `documented_resolution`
- `verification`

Optional fields:

- `unsafe_or_unnecessary`
- `tools_available`
- `scripted_tool_observations`
- `source_reference`
- `distractors`
- `task_metadata`

The generator writes visible `ScenarioCase` rows and hidden `AnswerKey` rows. Resolution steps are intentionally excluded from `surface_prompt` and placed in `gold_actions` and `acceptable_remediations`.
