---
name: debug
description: "Systematic hypothesis-driven debugging for complex bugs, intermittent failures, and performance problems. Usage: /tao:debug <issue description>"
context: fork
---

# Tao — Debug

Systematic debugging with hypothesis-driven investigation for complex bugs, intermittent issues, and performance problems.

## Argument handling

- Primary argument: issue description — everything in `$ARGUMENTS` after stripping flags
- `--error-logs=<text>`: paste error logs or stack traces directly
- `--files=<paths>`: comma-separated paths for the agent to read
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt
- `--focus-areas=<areas>`: constrain investigation to these areas

## Dispatch

```text
Agent(
  subagent_type="tao:debug-investigator",
  model="opus",
  prompt="Debug this issue: <issue from $ARGUMENTS>

[If --error-logs: 'Error logs:\n<logs>']
[If --files: 'Relevant files: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each hypothesis step. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
