---
name: think
description: "Deep reasoning, optionally with vetting sub-agents"
---

# Tao — Think

Deep reasoning for complex problems. Merges what were previously two separate commands:

- **Default**: full pipeline — problem decomposition → proposal development → vetting via `proposal-vetting-judge` → final recommendation with confidence levels. Formerly `/tao:think`.
- **`--quick`**: multi-stage reasoning without the vetting stage — hard algorithms, architecture decisions, security threat modeling, multi-variable optimization. Formerly `/tao:thinkdeep`. Use when you want the reasoning without paying for a second vetting pass — e.g. the problem is more "work through this carefully" than "stress-test a decision."

## Argument handling

- Primary argument: problem or question — everything in `$ARGUMENTS` after stripping flags
- `--quick`: skip the vetting stage (dispatches `tao:deep-reasoner` instead of `tao:thinker`)
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain analysis to these aspects
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch — default (with vetting)

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

## Dispatch — `--quick` (no vetting)

```text
Agent(
  subagent_type="tao:deep-reasoner",
  model="opus",
  prompt="<problem from $ARGUMENTS>

[If --files: 'Analyze these files: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each analysis step. Budget 32,000 thinking tokens per step.']

Format your response as:
## Bottom Line
One or two sentences stating your conclusion or recommendation upfront.

## Problem Framing
How you're interpreting the problem and any key constraints.

## Analysis
Layered reasoning — work through the problem systematically. Use sub-sections as needed.

## Confidence & Caveats
Confidence level (High / Medium / Low) and any important unknowns or assumptions."
)
```
