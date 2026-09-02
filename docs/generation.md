# Dataset Generation From Documented Issues

Documented issue/resolution records are useful seed material, but the benchmark must not leak the fix in the visible prompt.

Use this command:

```powershell
uv run dedutive scenario generate `
  --source data/sources/issues_resolutions.example.jsonl `
  --output-scenarios data/scenarios/generated.jsonl `
  --output-answers data/answers/generated_answer_key.jsonl `
  --variants-per-source 3
```

Validate the result:

```powershell
uv run dedutive scenario validate `
  --scenarios data/scenarios/generated.jsonl `
  --answers data/answers/generated_answer_key.jsonl
```

## Source Format

Each JSONL row describes one documented issue:

```json
{
  "source_id": "kb-001",
  "title": "Trust relationship failed after workstation restore",
  "task_family": "identity_auth",
  "issue_summary": "User cannot sign in to a restored domain-joined workstation.",
  "symptoms": [
    "Logon screen shows a trust relationship failure",
    "Device was restored from backup two days ago"
  ],
  "documented_root_cause": "machine account password out of sync after restore",
  "documented_resolution": [
    "Log in with cached or local admin credentials",
    "Test secure channel",
    "Repair secure channel",
    "Verify domain logon"
  ],
  "verification": [
    "Domain logon succeeds",
    "Secure channel reports healthy"
  ],
  "unsafe_or_unnecessary": [
    "Wipe and rebuild immediately",
    "Blame DNS without evidence"
  ]
}
```

## Permutations

The generator varies framework, ambiguity, evidence quality, access constraints, blast radius, time pressure, and risk profile. The visible scenario gets symptoms and operational constraints. The hidden answer key gets root cause, remediation, unsafe actions, and verification requirements.

Use `--frameworks kt,fordec,rpd` to control framework cycling and `--policies baseline_a,baseline_b` to attach policy labels for later analysis.
