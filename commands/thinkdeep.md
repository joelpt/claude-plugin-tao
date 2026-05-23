---
name: thinkdeep
description: "Multi-stage deep reasoning for complex problems — algorithms, architecture, security threat modeling, multi-variable optimization. Usage: /tao:thinkdeep <problem>"
context: fork
---

# Tao — Think Deep

Multi-stage deep reasoning for complex problems: hard algorithms, architecture decisions, security threat modeling, and multi-variable optimization.

## Argument handling

- Primary argument: everything in `$ARGUMENTS` after stripping flags
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt
- `--files=<paths>`: comma-separated paths for the agent to read
- `--focus-areas=<areas>`: constrain analysis to these areas

## Dispatch

```text
Agent(
  subagent_type="tao:deep-reasoner",
  model="opus",
  prompt="<problem from $ARGUMENTS>

[If --files: 'Analyze these files: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each analysis step. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
