---
name: tracer
description: "Code flow and dependency tracing — analyzes execution paths, data flow, dependencies, and provides instrumentation strategies. Usage: /tao:tracer [--files=<paths>] <function or flow to trace>"
---

# Tao — Execution Tracer

Code flow and dependency tracing: analyzes execution paths, data flow, dependencies, and provides instrumentation strategies for understanding complex systems.

## Argument handling

- Primary argument: function, method, or flow to trace — from `$ARGUMENTS` after stripping flags
- `--files=<paths>`: files/directories to trace through
- `--focus-areas=<areas>`: specific tracing aspects (e.g. data flow, error paths, async boundaries)
- `--prompt=<text>`: specific tracing question

## Dispatch

```text
Agent(
  subagent_type="tao:execution-tracer",
  model="sonnet",
  prompt="Trace the execution flow and dependencies.

[If freeform: 'Entry point / flow: <text>']
[If --files: 'Codebase files: <paths>']
[If --focus-areas: 'Focus on: <areas>']

Format your response as:
## Entry Point
Where execution begins — function signature, triggering event, or API endpoint.

## Execution Flow
Step-by-step trace of the call chain. Use a numbered list or ASCII flowchart. For each step: what is called, what data passes through, what side effects occur.

## Key Dependencies
External services, databases, caches, or modules this flow depends on, with notes on failure modes.

## Data Transformations
How the primary data object changes shape as it moves through the flow.

## Instrumentation Points
Where to add logging, metrics, or breakpoints to observe this flow in production or during debugging."
)
```
