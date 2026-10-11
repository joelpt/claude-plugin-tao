# Vet — Standard depth (3 voices — Claude + Grok + a local model)

Dispatch all three in ONE message (parallel tool calls).

**Passing the input to a Bash voice.** Give the text to `llm_call.py` through a *quoted heredoc* whose delimiter is a fresh random token you invent for each call (for example `TAO_7QK2M9_EOF`), never a fixed literal. A double-quoted shell string would execute backticks and `$(...)` inside the vetted text, and a fixed delimiter can collide with a line of the input. Replace `<input>` with the text itself, verbatim.

**Voice 1 — Claude Skeptic** (Agent tool):

```text
Agent(
  subagent_type="tao:senior-skeptic-reviewer",
  model="opus",
  prompt="Review this as a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright? Be constructive but direct. Where the claim is about this codebase, ground your critique in the actual files — read them, don't reason abstractly.\n\n<input>\n\n[If --files: 'Relevant context files: <paths>']\n[If --focus-areas: 'Focus on: <areas>']\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]]. Budget 32,000 thinking tokens.']"
)
```

**Voice 2 — Grok Challenger** (Bash tool — self-contained; this is a separate tool call from Voice 1/3, so it resolves its own paths rather than relying on any earlier `Bash` call's shell state):

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"
SCRIPTS="$PLUGIN_ROOT/scripts"
CONFIG="$PLUGIN_ROOT/config/models.json"
python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.standard.challenger \
  --system="Be a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright?" \
  --max-tokens=<4096 standard | 16384 high-effort> <<'TAO_RANDOM_EOF'
<input>
TAO_RANDOM_EOF
```

**Voice 3 — Local model** (Bash tool — self-contained, same reason). Set the Bash tool's `timeout` to `600000` (10 minutes): a local 27-31B model can take minutes on a plan-sized prompt, and the default 120 s would kill the call.

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"
SCRIPTS="$PLUGIN_ROOT/scripts"
CONFIG="$PLUGIN_ROOT/config/models.json"
python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.standard.local \
  --system="You are a senior skeptic. What are the biggest risks and wrong assumptions? What would you reject? Be direct." \
  --max-tokens=<8192 standard | 16384 high-effort> <<'TAO_RANDOM_EOF'
<input>
TAO_RANDOM_EOF
```

## Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — <the ERROR line the script printed>. Edit config/models.json to change provider.]`. The local voice's error line names the exact fix (for example `lms get`, `lms server start`, or raising the context length), so quote it rather than guessing a cause.

## Present results

Show all three responses as human-readable text with clear attribution, then a mechanical merge — no editorial layer, no recommendation unless the user asks for one.

```text
## Claude Opus
<claude response verbatim>

## Grok 4.3
<grok response verbatim, or "[Grok unavailable: check XAI_API_KEY in ~/.zshenv]">

## Local [provider/model]
<local response verbatim, or "[Local voice unavailable: <the error line>]">

## Points raised by multiple models
<deduplicated list — note which models raised each point, e.g. "(Claude, Grok)">

## Points raised by only one model
<list with attribution — potential unique insights or model-specific blind spots>

## Explicit disagreements
<only where models took directly opposing positions — quote both sides>
```

## Run stats

Extract `[tao-stats]` lines from Bash stderr (lines starting with `[tao-stats]`). Use `—` for the Claude voice. Take the Local row's provider and model from its stats line.

```text
## Run stats
| Voice   | Provider | Model        | Tokens in | Tokens out | Time   | Tok/s |
|---------|----------|--------------|-----------|------------|--------|-------|
| Claude  | claude   | opus         | —         | —          | —      | —     |
| Grok    | xai      | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
| Local   | <provider> | <model>    | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
```

If a voice was unavailable, omit its row or mark all cells `unavailable`.
