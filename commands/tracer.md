---
name: tracer
description: "Code flow and dependency tracing — analyzes execution paths, data flow, dependencies, and provides instrumentation strategies. Usage: /tao:tracer [--files=<paths>] <function or flow to trace>"
context: fork
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
[If --focus-areas: 'Focus on: <areas>']"
)
```

Present the agent's response directly to the user as formatted markdown.
