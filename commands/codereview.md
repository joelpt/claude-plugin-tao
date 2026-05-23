---
name: codereview
description: "Comprehensive code quality and security analysis — quality, security, performance, architecture, and actionable recommendations. Usage: /tao:codereview [--files=<paths>]"
context: fork
---

# Tao — Code Review

Comprehensive code quality and security analysis covering quality, security, performance, architecture, and actionable recommendations.

## Argument handling

- `--files=<paths>`: comma-separated file/directory paths to review (defaults to current git diff if omitted)
- `--focus-areas=<areas>`: constrain review to these areas (e.g. security, performance, maintainability)
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt
- Any freeform text in `$ARGUMENTS` is passed as additional context or instructions

## Dispatch

```text
Agent(
  subagent_type="tao:code-reviewer",
  model="opus",
  prompt="Review the following code for quality, security, and correctness.

[If --files: 'Files to review: <paths>']
[If no --files: 'Review the current git diff / staged changes.']
[If --focus-areas: 'Focus on: <areas>']
[If freeform text: '<text>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each section. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
