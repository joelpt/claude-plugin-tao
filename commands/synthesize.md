---
name: synthesize
description: "Reconcile multiple conflicting viewpoints, approaches, or solutions into a unified strategy. Usage: /tao:synthesize <description of the conflicting perspectives>"
context: fork
---

# Tao — Synthesize

Reconcile multiple conflicting viewpoints, approaches, or solutions into a unified strategy. Identifies synergies, evaluates second-order consequences, and formulates an optimal synthesis.

## Argument handling

- Primary argument: description of the conflicting perspectives or approaches — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: relevant files or docs presenting the different viewpoints
- `--focus-areas=<areas>`: specific aspects to prioritize in the synthesis
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:perspective-synthesizer",
  model="sonnet",
  prompt="Synthesize these conflicting perspectives into a unified strategy: <description from $ARGUMENTS>

[If --files: 'Relevant files/documents: <paths>']
[If --focus-areas: 'Prioritize: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for synthesis. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
