---
name: analyze
description: "Architecture and strategic code analysis — design patterns, scalability, technical debt, and improvement roadmaps. Uses 1M context window. Usage: /tao:analyze [--files=<paths>] <question>"
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
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each analysis phase. Budget 32,000 thinking tokens per step.']

Format your response as:
## Architecture Overview
How the system is structured — layers, modules, data flow, key boundaries.

## Patterns & Design
Design patterns in use, what they're solving, how consistently they're applied.

## Technical Debt
Current debt inventory, prioritized by impact. Be specific: file/module and what the debt costs.

## Recommendations
Prioritized improvements (P1 / P2 / P3). For each: what to change, why, estimated effort, risk of not doing it.

## Diagram (if helpful)
ASCII or mermaid diagram of a key relationship or flow worth visualizing."
)
```
