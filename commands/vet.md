---
name: vet
description: "Multi-perspective proposal vetting and validation — stress-tests decisions, architectural choices, and implementation plans before commitment. Usage: /tao:vet <proposal>"
context: fork
---

# Tao — Vet

Multi-perspective proposal vetting and validation. Stress-tests decisions, architectural choices, and implementation plans from multiple angles before commitment.

## Argument handling

- Primary argument: proposal to vet — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain vetting to specific concerns
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:proposal-vetting-judge",
  model="opus",
  prompt="Vet this proposal: <proposal from $ARGUMENTS>

[If --files: 'Relevant context files: <paths>']
[If --focus-areas: 'Focus vetting on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each vetting angle. Budget 32,000 thinking tokens per step.']

Format your final response as:
## Verdict
One of: ✅ Proceed | ⚠️ Proceed with modifications | ❌ Do not proceed
One sentence explaining the verdict.

## Strengths
What the proposal does well. Be specific.

## Risks & Concerns
Issues found, organized by severity (Critical / Major / Minor). For each: what the risk is, when it would manifest, how bad.

## Required Modifications (if Proceed with modifications)
Specific changes needed before this is safe to implement.

## Next Steps
What to do immediately after reading this.

Do not include internal sub-agent dialogue or intermediate JSON in the final response."
)
```
