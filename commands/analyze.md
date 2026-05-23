---
name: analyze
description: "Architecture and strategic code analysis — design patterns, scalability, technical debt, and improvement roadmaps. Uses 1M context window. Usage: /tao:analyze [--files=<paths>] <question>"
context: fork
---

# Tao — Analyze

Architecture and strategic code analysis covering design patterns, scalability, technical debt, and improvement roadmaps. Suited for large codebases requiring full context.

## Argument handling

- Primary argument: freeform question or analysis goal from `$ARGUMENTS`
- `--files=<paths>`: comma-separated file/directory paths to analyze
- `--focus-areas=<areas>`: constrain to specific architectural concerns
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:architecture-analyst",
  model="opus",
  prompt="Analyze the architecture and codebase.

[If freeform: '<question/goal>']
[If --files: 'Files/directories to analyze: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each analysis phase. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
