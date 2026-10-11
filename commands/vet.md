---
name: vet
description: "Vet a proposal, 1-3 voices, depth auto-picked"
---

# Tao — Vet

Multi-perspective proposal vetting and validation — merges what were previously four separate commands (`vet`, `challenge`, `skeptic`, `consensus`) into one depth dial. Stress-tests decisions, statements, architectural choices, and implementation plans before commitment.

The old command names (`/tao:challenge`, `/tao:skeptic`, `/tao:consensus`) no longer work in any form — not as standalone commands, not as `/tao <mode>` aliases (the bare router is gone too). The "Formerly" column below is a migration pointer only; use `--depth` to get the equivalent behavior.

## Depth levels

| Depth | Voices | Agent(s) | Formerly |
|---|---|---|---|
| quick | 1 — Claude only | `tao:proposal-vetting-judge` (opus) | `/tao:vet` |
| standard | 2 — Claude + Grok | `tao:senior-skeptic-reviewer` (opus) + Grok 4.3 | `/tao:challenge`, `/tao:skeptic` |
| full | 3 — Claude advocate + Grok critic + Codex/GPT analyst, synthesized | `tao:consensus-advocate` + external voices + `tao:consensus-synthesizer` | `/tao:consensus` |

## Argument handling

- Primary argument: proposal, statement, or decision to vet — everything in `$ARGUMENTS` after stripping flags
- `--depth=quick|standard|full` (or `--voices=1|2|3`): force a depth level, skipping Step 0
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain vetting to specific concerns
- `--high-effort` / `--thinking`: 16384 max_tokens for external calls; add ultrathink instruction to Claude agent(s)

## Step 0 — Decide depth (only when `--depth`/`--voices` is not given)

Read the input and classify it before dispatching. Judgment call, not a rigid rubric — weigh:

- **quick** — narrow and low-stakes, easily reversible if wrong (a naming choice, a small function's shape, a "does this look right" with no real downstream blast radius).
- **standard** — the default posture for most real vetting requests: architectural or design choices, "should we do X" questions, anything where being wrong costs real rework but isn't catastrophic, or where an external adversarial voice would plausibly catch something Claude alone would miss.
- **full** — high-stakes, hard-to-reverse, cross-system, security- or data-integrity-adjacent; or the user's own wording signals genuine indecision between competing options ("I can't decide between X and Y", "this is a big bet") or explicitly asks for consensus, a vote, or multiple independent opinions.

State the chosen depth and a one-sentence reason before dispatching (e.g. "Depth: standard — architectural choice with real but recoverable cost if wrong").

## Dispatch

**Note:** shell variables do not persist across separate tool calls, and the `Read` tool never expands `$VAR` in a path — it takes a literal string. So resolve the plugin root and load the depth's reference file in ONE self-contained `Bash` call (never split this across a `Bash` step and a later `Read` step):

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"
cat "$PLUGIN_ROOT/references/vet-<depth>.md"
```

(substitute `<depth>` with `quick`, `standard`, or `full`). This prints the exact `Agent()`/`Bash()` calls, role paths, results-handling, and output format for the chosen depth — follow it exactly, and do not construct the dispatch from memory or reuse another depth's template.

For standard/full, the printed reference's `Bash` calls also need `$SCRIPTS`/`$CONFIG` — since each of those is its own separate tool call too (dispatched in parallel, no shared shell state), the reference file includes the resolution inline in every `Bash` block that needs it. Don't strip it out when copying the command.
