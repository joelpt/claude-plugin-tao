---
name: think
description: "Deep reasoning, optionally with vetting sub-agents"
---

# Tao — Think

Deep reasoning for complex problems. Merges what were previously two separate commands:

- **Default**: full pipeline — problem decomposition → proposal development → vetting via `proposal-vetting-judge` → final recommendation with confidence levels. Formerly `/tao:think`.
- **`--quick`**: multi-stage reasoning without the vetting stage — hard algorithms, architecture decisions, security threat modeling, multi-variable optimization. Formerly the separate `/tao:thinkdeep` command, which no longer exists in any form (not standalone, not as a `/tao <mode>` alias) — use `/tao:think --quick` instead. Use when you want the reasoning without paying for a second vetting pass — e.g. the problem is more "work through this carefully" than "stress-test a decision."

## Argument handling

- Primary argument: problem or question — everything in `$ARGUMENTS` after stripping flags
- `--quick`: skip the vetting stage (dispatches `tao:deep-reasoner` instead of `tao:thinker`)
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain analysis to these aspects
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

**Note:** shell variables do not persist across separate tool calls, and the `Read` tool never expands `$VAR` in a path. Resolve the plugin root and load the variant's reference file in ONE self-contained `Bash` call — run exactly one of these two commands, whichever matches whether `--quick` was given:

```bash
# No --quick:
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; cat "$PLUGIN_ROOT/references/think-default.md"
```

```bash
# --quick given:
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; cat "$PLUGIN_ROOT/references/think-quick.md"
```

Follow the printed reference exactly — do not construct the dispatch from memory or reuse the other variant's template.
