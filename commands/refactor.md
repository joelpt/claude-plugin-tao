---
name: refactor
description: "Code smell detection and refactoring strategy — identifies anti-patterns, technical debt, and provides prioritized refactoring plans. Usage: /tao:refactor [--files=<paths>] [<focus>]"
context: fork
---

# Tao — Refactor

Code smell detection and refactoring strategy: identifies anti-patterns, technical debt, and provides prioritized refactoring plans with implementation guidance.

## Argument handling

- `--files=<paths>`: comma-separated file/directory paths to analyze (defaults to current working area)
- `--focus-areas=<areas>`: constrain to specific code quality concerns (e.g. coupling, duplication, complexity)
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt
- Freeform text in `$ARGUMENTS` treated as additional context or refactoring goal

## Dispatch

```text
Agent(
  subagent_type="tao:refactoring-advisor",
  model="sonnet",
  prompt="Identify code smells and provide a refactoring strategy.

[If --files: 'Files to analyze: <paths>']
[If freeform: '<goal/context>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for analysis. Budget 32,000 thinking tokens per step.']

Format your response as:
## Smell Inventory
Ranked by impact (highest first). For each smell: name, location (file:line range), why it hurts, rough effort to fix (S/M/L).

## Refactoring Strategy
The overall approach — what to attack first and in what order. Explain dependencies between refactors (e.g. 'extract X before collapsing Y').

## Step-by-Step Plan
Concrete numbered steps. Each step: what to do, which files change, what to test afterward.

## Risk Assessment
What could go wrong during this refactor and how to mitigate it (e.g. missing tests, tightly coupled consumers, hot code paths)."
)
```
