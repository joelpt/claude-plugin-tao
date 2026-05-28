---
name: skeptic
description: "3-voice constructive skepticism: Claude Opus + Grok 4.3 + Ollama probe a proposal for risks and wrong assumptions. Usage: /tao:skeptic <proposal to scrutinize>"
---

# Tao — Skeptic

3-voice constructive skepticism for stress-testing proposals, designs, and decisions before commitment.
Runs Claude, Grok, and Ollama in parallel — each independently reviews the proposal as a senior skeptic.

Voices:

- **Claude Opus** (primary skeptic) — constructive skepticism grounded in the codebase and evidence
- **Grok 4.3** (external sharp critic) — what would you reject outright? What could go wrong?
- **Ollama** (local) — independent local perspective, model set by `_default_local_model` in `config/models.json`

## Setup

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

## Step 1 — Parse arguments

The proposal is everything in `$ARGUMENTS` after stripping flags.

Recognized flags:

- `--high-effort` → use 16384 max_tokens for external calls and include `[[ ultrathink ]]` in Claude prompt

## Step 2 — Dispatch all 3 voices in ONE message (parallel)

**Voice 1 — Claude Skeptic** (Agent tool):

```text
Agent(
  subagent_type="tao:senior-skeptic-reviewer",
  model="opus",
  prompt="Review this proposal as a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright? Be constructive but direct.\n\n<proposal>\n\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]]. Budget 32,000 thinking tokens.']"
)
```

**Voice 2 — Grok Sharp Critic** (Bash tool):

```bash
printf '%s\n' "<proposal>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=skeptic.challenger \
  --system="Be a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright?" \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 3 — Ollama Local** (Bash tool):

```bash
printf '%s\n' "<proposal>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=skeptic.local \
  --system="You are a senior skeptic. What are the biggest risks and wrong assumptions? What would you reject? Be direct." \
  --max-tokens=<8192 standard | 16384 high-effort>
```

## Step 3 — Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — check API key or Ollama. Edit config/models.json to change provider.]`

## Step 4 — Present results

Show all three responses as human-readable text with clear attribution. Then append a mechanical merge — no editorial layer, no recommendation unless the user asks for one.

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

After the synthesis, append the run stats table. Extract `[tao-stats]` lines from Bash stderr (lines starting with `[tao-stats]`). Use `—` for the Claude voice.

```text
## Run stats
| Voice   | Provider | Model        | Tokens in | Tokens out | Time   | Tok/s |
|---------|----------|--------------|-----------|------------|--------|-------|
| Claude  | claude   | opus         | —         | —          | —      | —     |
| Grok    | xai      | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
| Ollama  | ollama   | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
```

If a voice was unavailable, omit its row or mark all cells `unavailable`.
