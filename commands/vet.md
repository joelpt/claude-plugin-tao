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
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each vetting angle. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
