---
name: think
description: "Deep reasoning with automatic rigorous vetting via sub-agents — problem decomposition, proposal development, vetting, and final recommendation with confidence levels. Usage: /tao:think <problem or question>"
---

# Tao — Think

Deep reasoning with rigorous vetting: problem decomposition → proposal development → vetting via proposal-vetting-judge → final recommendation with confidence levels.

## Argument handling

- Primary argument: problem or question — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain analysis to these aspects
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:thinker",
  model="opus",
  prompt="<problem/question from $ARGUMENTS>

[If --files: 'Relevant files: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each reasoning stage. Budget 32,000 thinking tokens per step.']

Format your final response as:
## Problem Decomposition
The key sub-problems and constraints you identified.

## Proposed Approach
Your recommended solution or answer, stated clearly.

## Vetting Concerns
The strongest objections to your approach and how you addressed them. If the vetting sub-agent found something you couldn't resolve, say so explicitly.

## Recommendation
Final answer with confidence level: High (I'd stake a production deploy on this) / Medium (solid but watch for X) / Low (best available answer but significant uncertainty remains).

Self-contained output (mandatory): the caller sees ONLY this response — not this prompt, the sub-agent dialogue, or intermediate JSON. Define every option, alternative, or position IN FULL (20–400 words each; err verbose) before any conclusion references it. Never report 'X is best / Y was rejected' without first showing the reader what X and Y are."
)
```
