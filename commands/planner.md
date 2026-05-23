---
name: planner
description: "Structured task planning with scope definition, strategy, and detailed execution phases. Usage: /tao:planner <task description>"
context: fork
---

# Tao — Planner

Structured task planning with scope definition, strategy development, and detailed execution plans with phases, dependencies, and milestones.

## Argument handling

- Primary argument: task description — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: relevant files or directories for context
- `--focus-areas=<areas>`: constrain planning to specific aspects
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:task-planner",
  model="opus",
  prompt="Create a structured execution plan for: <task from $ARGUMENTS>

[If --files: 'Relevant context files: <paths>']
[If --focus-areas: 'Focus planning on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each planning phase. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
