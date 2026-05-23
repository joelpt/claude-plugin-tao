---
name: precommit
description: "Validate git changes before commit — quality, security, compliance, and commit readiness with actionable recommendations. Usage: /tao:precommit"
context: fork
---

# Tao — Pre-commit Validator

Git change validation before commit: analyzes staged changes for quality, security, compliance, and commit readiness with actionable recommendations.

## Argument handling

- No primary argument required — operates on current git staged/unstaged changes
- `--files=<paths>`: limit analysis to specific files
- `--focus-areas=<areas>`: constrain to specific validation concerns (e.g. security, style, logic)
- Freeform text in `$ARGUMENTS` treated as additional context

## Dispatch

```text
Agent(
  subagent_type="tao:precommit-validator",
  model="sonnet",
  prompt="Validate the current git changes for commit readiness.

[If --files: 'Limit to: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If freeform: '<context>']"
)
```

Present the agent's response directly to the user as formatted markdown.
