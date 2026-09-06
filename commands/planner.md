---
name: planner
description: "Structured task planning with execution phases"
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
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each planning phase. Budget 32,000 thinking tokens per step.']

Format your response as a phased execution plan:

## Scope
What's in and out. Key assumptions.

## Phase N — <Name>
For each phase:
- Goal: what done looks like
- Steps: ordered list of concrete actions
- Dependencies: what must be true before this phase starts
- Milestone: how to verify the phase is complete
- Estimated effort: rough t-shirt size (S/M/L/XL)

## Risks & Blockers
What could derail this plan and how to mitigate each.

## Open Questions
Decisions that need to be made before or during execution."
)
```
