---
name: requirements
description: "Requirements discovery and technical translation — surfaces implicit requirements, translates business goals to technical specs, and evaluates approaches. Usage: /tao:requirements <feature or goal>"
context: fork
---

# Tao — Requirements

Requirements discovery and technical translation: surfaces implicit requirements, identifies potential challenges, translates business goals into concrete technical specifications, and makes compelling arguments for proposed solutions.

## Argument handling

- Primary argument: feature, goal, or vague idea — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: existing codebase files for context
- `--focus-areas=<areas>`: specific requirement dimensions to probe (e.g. performance, security, UX)
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:requirements-architect",
  model="sonnet",
  prompt="Discover and translate requirements for: <feature/goal from $ARGUMENTS>

[If --files: 'Existing codebase context: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for requirements discovery. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
