---
name: vet
description: "Vet a proposal, 1-4 voices, depth auto-picked"
---

# Tao — Vet

Multi-perspective proposal vetting and validation — merges what were previously four separate commands (`vet`, `challenge`, `skeptic`, `consensus`) into one depth dial. Stress-tests decisions, statements, architectural choices, and implementation plans before commitment.

## Depth levels

| Depth | Voices | Agent(s) | Formerly |
|---|---|---|---|
| quick | 1 — Claude only | `tao:proposal-vetting-judge` (opus) | `/tao:vet` |
| standard | 3 — Claude + Grok + Ollama | `tao:senior-skeptic-reviewer` (opus) + Grok 4.3 + Ollama | `/tao:challenge`, `/tao:skeptic` |
| full | 4 — Claude advocate + Grok critic + Codex/GPT analyst + Ollama, synthesized | `tao:consensus-advocate` + external voices + `tao:consensus-synthesizer` | `/tao:consensus` |

## Argument handling

- Primary argument: proposal, statement, or decision to vet — everything in `$ARGUMENTS` after stripping flags
- `--depth=quick|standard|full` (or `--voices=1|3|4`): force a depth level, skipping Step 0
- `--files=<paths>`: relevant files for context
- `--focus-areas=<areas>`: constrain vetting to specific concerns
- `--high-effort` / `--thinking`: 16384 max_tokens for external calls; add ultrathink instruction to Claude agent(s)

## Step 0 — Decide depth (only when `--depth`/`--voices` is not given)

Read the input and classify it before dispatching. Judgment call, not a rigid rubric — weigh:

- **quick** — narrow and low-stakes, easily reversible if wrong (a naming choice, a small function's shape, a "does this look right" with no real downstream blast radius).
- **standard** — the default posture for most real vetting requests: architectural or design choices, "should we do X" questions, anything where being wrong costs real rework but isn't catastrophic, or where an external adversarial voice would plausibly catch something Claude alone would miss.
- **full** — high-stakes, hard-to-reverse, cross-system, security- or data-integrity-adjacent; or the user's own wording signals genuine indecision between competing options ("I can't decide between X and Y", "this is a big bet") or explicitly asks for consensus, a vote, or multiple independent opinions.

State the chosen depth and a one-sentence reason before dispatching (e.g. "Depth: standard — architectural choice with real but recoverable cost if wrong").

## Setup

Resolve the plugin root — needed to locate the reference file below for every depth (standard/full also reuse `$SCRIPTS`/`$CONFIG` for their external LLM calls):

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

## Dispatch

Read `$SCRIPTS/../references/vet-<depth>.md` for the exact Agent()/Bash() calls, role paths, results-handling, and output format for the chosen depth:

- `$SCRIPTS/../references/vet-quick.md`
- `$SCRIPTS/../references/vet-standard.md`
- `$SCRIPTS/../references/vet-full.md`

Do not construct the dispatch from memory or reuse another depth's template — each depth's exact prompts, role paths, and output formatting live only in its own reference file.
