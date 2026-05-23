---
name: think
description: "Deep reasoning with automatic rigorous vetting via sub-agents — problem decomposition, proposal development, vetting, and final recommendation with confidence levels. Usage: /tao:think <problem or question>"
context: fork
---

# Tao — Think

Deep reasoning with rigorous vetting: problem decomposition → proposal development → vetting via proposal-vetting-judge → final recommendation with confidence levels.

## Argument handling

- Primary argument: problem or question — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain analysis to these aspects
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:thinker",
  model="opus",
  prompt="<problem/question from $ARGUMENTS>

[If --files: 'Relevant files: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each reasoning stage. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
