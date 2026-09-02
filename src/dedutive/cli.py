from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from dedutive.data import (
    DEFAULT_ANSWERS,
    DEFAULT_REASONING_STRATEGIES,
    DEFAULT_SCENARIOS,
    DEFAULT_STAGE_POLICIES,
    DEFAULT_TOOL_CATALOG,
    load_answer_keys,
    load_cases,
    load_frameworks,
    load_policies,
    load_tool_catalog,
    validate_dataset_alignment,
    write_jsonl,
)
from dedutive.evaluation.scoring import create_bandit_log_records, score_run_records
from dedutive.generation import generate_from_documented_issues, load_documented_issues
from dedutive.orchestrator.config import build_session_from_config, load_experiment_config
from dedutive.orchestrator.runtime import run_case
from dedutive.providers.openai_compatible import OpenAICompatibleProvider
from dedutive.scenarios.prompts import render_session_prompt, session_to_stage_policy


app = typer.Typer(help="Dedutive: a configurable IT troubleshooting orchestration architecture.")
scenario_app = typer.Typer(help="Scenario dataset commands.")
frameworks_app = typer.Typer(help="Strategy and stage-policy inspection commands.")
experiment_app = typer.Typer(help="Run controlled experiments across configurations.")
app.add_typer(scenario_app, name="scenario")
app.add_typer(frameworks_app, name="frameworks")
app.add_typer(experiment_app, name="experiment")


@scenario_app.command("validate")
def scenario_validate(
    scenarios: Annotated[Path, typer.Option(help="Scenario JSONL path.")] = DEFAULT_SCENARIOS,
    answers: Annotated[Path, typer.Option(help="Answer-key JSONL path.")] = DEFAULT_ANSWERS,
) -> None:
    cases = load_cases(scenarios)
    answer_keys = load_answer_keys(answers)
    validate_dataset_alignment(cases, answer_keys)
    typer.echo(f"Validated {len(cases)} cases and {len(answer_keys)} answer keys.")


@scenario_app.command("new")
def scenario_new(
    scenario_id: Annotated[str, typer.Argument(help="Scenario ID, for example IDAUTH-011.")],
    title: Annotated[str, typer.Argument(help="Human title.")],
    output: Annotated[Path | None, typer.Option(help="Optional JSON template output file.")] = None,
) -> None:
    template = {
        "scenario": {
            "case_id": f"{scenario_id}-kt",
            "scenario_id": scenario_id,
            "title": title,
            "framework": "kt",
            "governance_mode": "autonomous",
            "briefing_mode": "nits",
            "learning_mode": "single_loop",
            "task_family": "identity_auth",
            "complexity": "moderate",
            "ambiguity_level": "medium",
            "blast_radius": "single_device",
            "time_pressure": "urgent",
            "change_recency": "recent_change",
            "access_constraints": ["remote_only"],
            "evidence_quality": "noisy",
            "risk_profile": "medium",
            "tool_profile": "basic_endpoint",
            "surface_prompt": "Describe only the visible incident symptoms here.",
            "environment_facts_visible": {},
            "tools_available": ["envsense"],
            "distractors": [],
            "scripted_tool_observations": [],
        },
        "answer_key": {
            "case_id": f"{scenario_id}-kt",
            "root_cause": "hidden_root_cause",
            "acceptable_remediations": ["least_disruptive_valid_fix"],
            "gold_evidence": ["discriminating evidence"],
            "gold_actions": ["minimum required action"],
            "unsafe_actions": ["unsupported destructive action"],
            "verification_requirements": ["observable fixed condition"],
        },
    }
    rendered = json.dumps(template, indent=2)
    if output is None:
        typer.echo(rendered)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        typer.echo(f"Wrote scenario template to {output}")


@scenario_app.command("generate")
def scenario_generate(
    source: Annotated[Path, typer.Option("--source", help="Documented issue/resolution JSONL source.")],
    output_scenarios: Annotated[Path, typer.Option("--output-scenarios", help="Generated visible scenario JSONL output.")],
    output_answers: Annotated[Path, typer.Option("--output-answers", help="Generated hidden answer-key JSONL output.")],
    variants_per_source: Annotated[int, typer.Option("--variants-per-source", help="Variants to generate for each source issue.")] = 3,
    frameworks: Annotated[str, typer.Option("--frameworks", help="Comma-separated framework cycle.")] = "kt,fordec,rpd",
    policies: Annotated[str | None, typer.Option("--policies", help="Optional comma-separated policy variant labels to attach.")] = None,
) -> None:
    selected_frameworks = [item.strip() for item in frameworks.split(",") if item.strip()]
    selected_policies = [item.strip() for item in policies.split(",") if item.strip()] if policies else []
    issues = load_documented_issues(source)
    cases, answers = generate_from_documented_issues(
        issues,
        variants_per_source=variants_per_source,
        frameworks=selected_frameworks,
        policies=selected_policies,
    )
    write_jsonl(output_scenarios, [case.model_dump(mode="json") for case in cases])
    write_jsonl(output_answers, [answer.model_dump(mode="json") for answer in answers])
    typer.echo(
        f"Generated {len(cases)} scenarios and {len(answers)} answer keys from {len(issues)} documented issues."
    )


@frameworks_app.command("list")
def frameworks_list(
    policies_path: Annotated[Path, typer.Option("--policies", help="Stage policy JSON path.")] = DEFAULT_STAGE_POLICIES,
    frameworks_path: Annotated[Path, typer.Option("--frameworks", help="Reasoning strategy JSON path.")] = DEFAULT_REASONING_STRATEGIES,
) -> None:
    typer.echo("Strategy dimensions: reasoning, governance, decision, communication, learning")
    frameworks = load_frameworks(frameworks_path)
    loaded = load_policies(policies_path, frameworks)
    for policy in loaded.values():
        assignments = ", ".join(f"{stage}={arm}" for stage, arm in policy.stage_assignments.items())
        typer.echo(f"{policy.policy_id}\t{assignments}\t{policy.description}")


@app.command()
def inspect(
    experiment: Annotated[Path, typer.Argument(help="Experiment YAML config path.")],
    limit: Annotated[int | None, typer.Option(help="Maximum prompts to render.")] = None,
    scenarios: Annotated[Path, typer.Option(help="Scenario JSONL path.")] = DEFAULT_SCENARIOS,
    frameworks_path: Annotated[Path, typer.Option("--frameworks", help="Reasoning strategy JSON path.")] = DEFAULT_REASONING_STRATEGIES,
    tools_path: Annotated[Path, typer.Option("--tools", help="Tool catalog JSON path.")] = DEFAULT_TOOL_CATALOG,
) -> None:
    cases = load_cases(scenarios)
    frameworks = load_frameworks(frameworks_path)
    tools = load_tool_catalog(tools_path)
    config = load_experiment_config(experiment)
    selected = cases[:limit] if limit is not None else cases
    for case in selected:
        session = build_session_from_config(config, case)
        typer.echo(f"## {case.case_id}")
        for message in render_session_prompt(session, frameworks, tools):
            typer.echo(f"[{message['role']}]\n{message['content']}\n")


@app.command()
def run(
    experiment: Annotated[Path, typer.Option("--experiment", help="Experiment YAML config path.")],
    output: Annotated[Path | None, typer.Option(help="Run JSONL output path.")] = None,
    limit: Annotated[int | None, typer.Option(help="Maximum cases to run.")] = None,
    provider_name: Annotated[str, typer.Option("--provider", help="Provider name.")] = "openai_compatible",
    model: Annotated[str | None, typer.Option(help="Model name.")] = None,
    temperature: Annotated[float, typer.Option(help="Generation temperature.")] = 0.0,
    max_turns: Annotated[int, typer.Option(help="Maximum tool investigation turns.")] = 4,
    scenarios: Annotated[Path, typer.Option(help="Scenario JSONL path.")] = DEFAULT_SCENARIOS,
    frameworks_path: Annotated[Path, typer.Option("--frameworks", help="Reasoning strategy JSON path.")] = DEFAULT_REASONING_STRATEGIES,
    tools_path: Annotated[Path, typer.Option("--tools", help="Tool catalog JSON path.")] = DEFAULT_TOOL_CATALOG,
) -> None:
    load_dotenv()
    if provider_name != "openai_compatible":
        raise typer.BadParameter(f"unknown provider: {provider_name}")
    model_name = model or os.getenv("OPENAI_COMPATIBLE_MODEL")
    if not model_name:
        raise typer.BadParameter("model or OPENAI_COMPATIBLE_MODEL is required")

    provider = OpenAICompatibleProvider()
    frameworks = load_frameworks(frameworks_path)
    tools = load_tool_catalog(tools_path)
    config = load_experiment_config(experiment)
    cases = load_cases(scenarios)
    selected = cases[:limit] if limit is not None else cases
    rows = []
    for case in selected:
        session = build_session_from_config(config, case)
        policy = session_to_stage_policy(session)
        record = run_case(
            case,
            frameworks=frameworks,
            tool_catalog=tools,
            provider=provider,
            model=model_name,
            policy=policy,
            temperature=temperature,
            max_turns=max_turns,
        )
        rows.append(record.model_dump(mode="json"))
        typer.echo(f"Ran {case.case_id}")

    if output is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = Path("runs") / f"run_{stamp}.jsonl"
    write_jsonl(output, rows)
    typer.echo(f"Wrote {len(rows)} records to {output}")


@app.command()
def evaluate(
    run: Annotated[Path, typer.Option("--run", help="Run JSONL to score.")],
    scenarios: Annotated[Path, typer.Option(help="Scenario JSONL path.")] = DEFAULT_SCENARIOS,
    answers: Annotated[Path, typer.Option(help="Answer-key JSONL path.")] = DEFAULT_ANSWERS,
    output: Annotated[Path | None, typer.Option(help="Optional score JSONL output.")] = None,
    bandit_log: Annotated[Path | None, typer.Option("--bandit-log", help="Optional bandit-ready JSONL log output.")] = None,
    policies_path: Annotated[Path, typer.Option("--policies", help="Stage policy JSON path.")] = DEFAULT_STAGE_POLICIES,
    frameworks_path: Annotated[Path, typer.Option("--frameworks", help="Reasoning strategy JSON path.")] = DEFAULT_REASONING_STRATEGIES,
) -> None:
    cases = load_cases(scenarios)
    answer_keys = load_answer_keys(answers)
    scores = score_run_records(run, cases, answer_keys)
    for score_row in scores:
        typer.echo(f"{score_row.case_id}\t{score_row.total_score}\t{','.join(score_row.penalties) or 'ok'}")
    if output is not None:
        write_jsonl(output, [score_row.model_dump(mode="json") for score_row in scores])
    if bandit_log is not None:
        frameworks = load_frameworks(frameworks_path)
        policies_by_id = load_policies(policies_path, frameworks)
        bandit_records = create_bandit_log_records(scores, cases, policies_by_id)
        write_jsonl(bandit_log, [record.model_dump(mode="json") for record in bandit_records])
        typer.echo(f"Wrote {len(bandit_records)} bandit log rows to {bandit_log}")


@experiment_app.command("compare")
def experiment_compare(
    experiments: Annotated[str, typer.Option("--experiments", help="Comma-separated experiment YAML paths.")],
    scenarios: Annotated[Path, typer.Option(help="Scenario JSONL path.")] = DEFAULT_SCENARIOS,
    answers: Annotated[Path, typer.Option(help="Answer-key JSONL path.")] = DEFAULT_ANSWERS,
    provider_name: Annotated[str, typer.Option("--provider", help="Provider name.")] = "openai_compatible",
    model: Annotated[str | None, typer.Option(help="Model name.")] = None,
    limit: Annotated[int | None, typer.Option(help="Maximum cases per experiment.")] = None,
    frameworks_path: Annotated[Path, typer.Option("--frameworks", help="Reasoning strategy JSON path.")] = DEFAULT_REASONING_STRATEGIES,
    tools_path: Annotated[Path, typer.Option("--tools", help="Tool catalog JSON path.")] = DEFAULT_TOOL_CATALOG,
) -> None:
    from dedutive.evaluation.scoring import score_record

    load_dotenv()
    model_name = model or os.getenv("OPENAI_COMPATIBLE_MODEL")
    if not model_name:
        raise typer.BadParameter("model or OPENAI_COMPATIBLE_MODEL is required")

    provider = OpenAICompatibleProvider()
    frameworks = load_frameworks(frameworks_path)
    tools = load_tool_catalog(tools_path)
    cases = load_cases(scenarios)
    answer_keys = load_answer_keys(answers)
    selected = cases[:limit] if limit is not None else cases

    for experiment_path in [item.strip() for item in experiments.split(",") if item.strip()]:
        config = load_experiment_config(Path(experiment_path))
        total = 0
        count = 0
        for case in selected:
            session = build_session_from_config(config, case)
            policy = session_to_stage_policy(session)
            record = run_case(
                case,
                frameworks=frameworks,
                tool_catalog=tools,
                provider=provider,
                model=model_name,
                policy=policy,
            )
            score = score_record(record, case, answer_keys[case.case_id])
            total += score.total_score
            count += 1
        mean_score = total / count if count else 0.0
        typer.echo(f"{experiment_path}\tmean_score={mean_score:.2f}\tcases={count}")


def main() -> None:
    app()
