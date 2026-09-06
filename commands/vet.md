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

## Setup (standard/full only — quick makes no external calls)

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

## Quick (1 voice)

```text
Agent(
  subagent_type="tao:proposal-vetting-judge",
  model="opus",
  prompt="Vet this proposal: <input from $ARGUMENTS>

[If --files: 'Relevant context files: <paths>']
[If --focus-areas: 'Focus vetting on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each vetting angle. Budget 32,000 thinking tokens per step.']

Format your final response as:
## Verdict
One of: ✅ Proceed | ⚠️ Proceed with modifications | ❌ Do not proceed
One sentence explaining the verdict.

## Strengths
What the proposal does well. Be specific.

## Risks & Concerns
Issues found, organized by severity (Critical / Major / Minor). For each: what the risk is, when it would manifest, how bad.

## Required Modifications (if Proceed with modifications)
Specific changes needed before this is safe to implement.

## Next Steps
What to do immediately after reading this.

Self-contained output (mandatory): the caller sees ONLY this response — not this prompt, the sub-agent dialogue, or intermediate JSON. Define every option, alternative, or position IN FULL (20–400 words each; err verbose) before any conclusion references it. Never report 'X is best / Y was rejected' without first showing the reader what X and Y are."
)
```

## Standard (3 voices — dispatch in ONE message, parallel)

**Voice 1 — Claude Skeptic** (Agent tool):

```text
Agent(
  subagent_type="tao:senior-skeptic-reviewer",
  model="opus",
  prompt="Review this as a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright? Be constructive but direct. Where the claim is about this codebase, ground your critique in the actual files — read them, don't reason abstractly.\n\n<input>\n\n[If --files: 'Relevant context files: <paths>']\n[If --focus-areas: 'Focus on: <areas>']\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]]. Budget 32,000 thinking tokens.']"
)
```

**Voice 2 — Grok Challenger** (Bash tool):

```bash
printf '%s\n' "<input>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.standard.challenger \
  --system="Be a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright?" \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 3 — Ollama Local** (Bash tool):

```bash
printf '%s\n' "<input>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.standard.local \
  --system="You are a senior skeptic. What are the biggest risks and wrong assumptions? What would you reject? Be direct." \
  --max-tokens=<8192 standard | 16384 high-effort>
```

Handle results, present, and run stats per the shared steps below.

## Full (4 voices — dispatch in ONE message, parallel)

**Voice 1 — Claude Advocate** (Agent tool):

```text
Agent(
  subagent_type="tao:consensus-advocate",
  model="opus",
  prompt="Argue FOR this decision. Make the strongest possible case for proceeding.\n\n<input>\n\n[If --files: 'Relevant context files: <paths>']\n[If --focus-areas: 'Focus on: <areas>']\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for analysis.']"
)
```

**Voice 2 — Grok Critic** (Bash tool):

```bash
printf '%s\n' "<input>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.full.critic \
  --system="Argue AGAINST this decision. Find flaws, risks, hidden costs, and failure modes. Be direct." \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 3 — Codex/GPT Analyst** (Bash tool):

```bash
printf '%s\n' "<input>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.full.analyst \
  --system="Provide neutral, balanced analysis of this decision. Weigh evidence objectively without advocacy." \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 4 — Ollama Local** (Bash tool):

```bash
printf '%s\n' "<input>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.full.local \
  --system="Provide your independent perspective on this decision. Focus on practical implementation realities." \
  --max-tokens=<8192 standard | 16384 high-effort>
```

Then synthesize:

```text
Agent(
  subagent_type="tao:consensus-synthesizer",
  model="opus",
  prompt="""Synthesize 4 perspectives on: <input>

## Claude Advocate (Claude Opus)
<advocate_response>

## Grok Critic (Grok 4.3)
<grok_response_or_unavailable>

## Codex/GPT Analyst
<codex_response_or_unavailable>

## Ollama Local Voice
<ollama_response_or_unavailable>

Note any unavailable voices and how that affects confidence.

Self-contained output (mandatory): the caller sees ONLY your response — never these four raw voices. Open with a 'Positions Considered' section defining each distinct option/stance the voices argued (20–400 words each; err verbose) before any recommendation references it. Never report 'option X is strongest / Y was rejected' without first showing the reader what X and Y are."""
)
```

## Handle results (standard/full)

For any Bash call that exits non-zero: substitute `[Voice unavailable — check API key or Ollama. Edit config/models.json to change provider.]`

## Present results (standard)

Show all three responses as human-readable text with clear attribution, then a mechanical merge — no editorial layer, no recommendation unless the user asks for one.

```text
## Claude Opus
<claude response verbatim>

## Grok 4.3
<grok response verbatim, or "[Grok unavailable: check XAI_API_KEY in ~/.zshenv]">

## Ollama [model-name]
<ollama response verbatim, or "[Ollama unavailable: check ollama serve is running]">

## Points raised by multiple models
<deduplicated list — note which models raised each point, e.g. "(Claude, Grok)">

## Points raised by only one model
<list with attribution — potential unique insights or model-specific blind spots>

## Explicit disagreements
<only where models took directly opposing positions — quote both sides>
```

## Run stats (standard)

Extract `[tao-stats]` lines from Bash stderr (lines starting with `[tao-stats]`). Use `—` for the Claude voice.

```text
## Run stats
| Voice   | Provider | Model        | Tokens in | Tokens out | Time   | Tok/s |
|---------|----------|--------------|-----------|------------|--------|-------|
| Claude  | claude   | opus         | —         | —          | —      | —     |
| Grok    | xai      | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
| Ollama  | ollama   | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
```

If a voice was unavailable, omit its row or mark all cells `unavailable`.

## Run stats (full)

Append after the synthesizer returns. `—` for Claude voices (no token telemetry available from Agent calls).

```text
## Run stats
| Voice         | Provider | Model         | Tokens in | Tokens out | Time   | Tok/s |
|---------------|----------|---------------|-----------|------------|--------|-------|
| Claude Opus   | claude   | opus          | —         | —          | —      | —     |
| Grok Critic   | xai      | <model>       | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
| Codex Analyst | codex    | <model>       | ?         | ?          | <Xs>   | n/a   |
| Ollama Local  | ollama   | <model>       | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
```

Omit rows for unavailable voices or mark all cells `unavailable`.
