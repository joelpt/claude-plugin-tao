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
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for synthesis. Budget 32,000 thinking tokens per step.']

Format your response as:
## The Core Tension
What is actually in conflict — the real disagreement beneath the surface-level options.

## What Each Side Gets Right
For each perspective: the valid insight or constraint it's optimizing for.

## Unified Recommendation
The synthesized approach that transcends the original options. Be concrete — state what to actually do.

## Trade-offs Accepted
What you're consciously giving up in this synthesis and why that's the right call.

## Implementation Path
First 2–3 concrete steps to move forward on the recommendation."
)
```
