---
name: consensus
description: "4-voice multi-LLM consensus analysis: Claude Opus (advocate) + Grok 4.3 (critic) + Codex/GPT (analyst) + Ollama local model (local). Usage: /tao:consensus <question or decision>"
context: fork
---

# Tao Consensus Mode

4-voice multi-LLM decision analysis for high-stakes architectural and design decisions.
Runs all voices in parallel for epistemic diversity, then synthesizes into a recommendation.

Voices:

- **Claude Opus** (advocate) — argues FOR. Free via Claude Max.
- **Grok 4.3** (critic) — argues AGAINST. xAI direct API.
- **Codex/GPT** (analyst) — neutral balanced analysis. OpenAI Codex CLI (subscription quota).
- **Ollama** (local) — independent local perspective. No cloud cost. Model set by `_default_local_model` in `config/models.json`.

Model assignments are configurable in `config/models.json` relative to `$TAO_SCRIPTS/..`.

## Setup

First, resolve paths:
```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

## Step 1 — Parse arguments

The question/decision is everything in `$ARGUMENTS` after stripping any flags.

Recognized flags:

- `--high-effort` → use 16384 max_tokens for external calls and include `[[ ultrathink ]]` in Claude prompts

## Step 2 — Dispatch all 4 voices in ONE message (parallel)

Run these 4 tool calls simultaneously:

**Voice 1 — Claude Advocate** (Agent tool):
```text
Agent(
  subagent_type="tao:consensus-advocate",
  model="opus",
  prompt="Argue FOR this decision. Make the strongest possible case for proceeding.\n\n<question>\n\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for analysis.']"
)
```

**Voice 2 — Grok Critic** (Bash tool):
```bash
printf '%s\n' "<question>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=consensus.critic \
  --system="Argue AGAINST this decision. Find flaws, risks, hidden costs, and failure modes. Be direct." \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 3 — Codex/GPT Analyst** (Bash tool):
```bash
printf '%s\n' "<question>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=consensus.analyst \
  --system="Provide neutral, balanced analysis of this decision. Weigh evidence objectively without advocacy." \
  --max-tokens=<4096 standard | 16384 high-effort>
```

**Voice 4 — Ollama Local** (Bash tool):
```bash
printf '%s\n' "<question>" | python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=consensus.local \
  --system="Provide your independent perspective on this decision. Focus on practical implementation realities." \
  --max-tokens=<8192 standard | 16384 high-effort>
```

## Step 3 — Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — check API key or Ollama. Edit config/models.json to change provider.]`

## Step 4 — Synthesize

```text
Agent(
  subagent_type="tao:consensus-synthesizer",
  model="opus",
  prompt="""Synthesize 4 perspectives on: <question>

## Claude Advocate (Claude Opus)
<advocate_response>

## Grok Critic (Grok 4.3)
<grok_response_or_unavailable>

## Codex/GPT Analyst
<codex_response_or_unavailable>

## Ollama Local Voice
<ollama_response_or_unavailable>

Note any unavailable voices and how that affects confidence."""
)
```

## Step 5 — Run stats

After the synthesizer returns, append a run summary table. Extract `[tao-stats]` lines from each Bash tool result's stderr (lines starting with `[tao-stats]`). Use `—` for Claude voices (no token telemetry available from Agent calls).

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
