---
name: challenge
description: "3-voice adversarial challenge: Claude Sonnet + Grok 4.3 + Ollama attack a statement from every angle. Usage: /tao:challenge <statement to challenge>"
context: fork
---

# Tao — Challenge

3-voice adversarial analysis for stress-testing statements, assumptions, and decisions.
Runs Claude, Grok, and Ollama in parallel — each independently challenges the statement.

Voices:

- **Claude Sonnet** (primary challenger) — evidence-based challenge from the codebase
- **Grok 4.3** (external adversarial) — sharp external critic, no holds barred
- **Ollama** (local) — independent local perspective, model set by `_default_local_model` in `config/models.json`

## Setup

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

## Step 1 — Parse arguments

The statement is everything in `$ARGUMENTS` after stripping flags.

Recognized flags:

- `--high-effort` → use 16384 max_tokens for external calls and include `[[ ultrathink ]]` in Claude prompt

## Step 2 — Dispatch all 3 voices in ONE message (parallel)

**Voice 1 — Claude Challenger** (Agent tool):

```text
Agent(
  subagent_type="tao:challenge-assessor",
  model="sonnet",
  prompt="Challenge this statement aggressively. Find every flaw, assumption, and risk. Be direct and specific.\n\n<statement>\n\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]]. Budget 32,000 thinking tokens.']"
)
```

**Voice 2 — Grok Challenger** (Bash tool):

```bash
printf '%s\n' "<statement>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=challenge.challenger \
  --system="Challenge this statement aggressively. Find every flaw, assumption, and risk. Be direct." \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 3 — Ollama Local** (Bash tool):

```bash
printf '%s\n' "<statement>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=challenge.local \
  --system="Challenge this statement. Identify every assumption, risk, and flaw. Be direct and specific." \
  --max-tokens=<8192 standard | 16384 high-effort>
```

## Step 3 — Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — check API key or Ollama. Edit config/models.json to change provider.]`

## Step 4 — Present results

Show all three responses as human-readable text with clear attribution. Then append a mechanical merge — no editorial layer, no recommendation unless the user asks for one.

```text
## Claude Sonnet
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
| Claude  | claude   | sonnet       | —         | —          | —      | —     |
| Grok    | xai      | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
| Ollama  | ollama   | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
```

If a voice was unavailable, omit its row or mark all cells `unavailable`.
