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

## Dispatch

Resolve the plugin root, then read the reference file for the chosen variant:

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
```

- No `--quick`: read `$SCRIPTS/../references/think-default.md`
- `--quick` given: read `$SCRIPTS/../references/think-quick.md`

Do not construct the dispatch from memory or reuse the other variant's template — each variant's exact prompt and output format lives only in its own reference file.
