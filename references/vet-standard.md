# Vet — Standard depth (2 voices — Claude + Grok)

Dispatch both in ONE message (parallel tool calls).

**Passing the input to a Bash voice.** Give the text to `llm_call.py` through a *quoted heredoc* whose delimiter is a fresh random token you invent for each call (for example `TAO_7QK2M9_EOF`), never a fixed literal. A double-quoted shell string would execute backticks and `$(...)` inside the vetted text, and a fixed delimiter can collide with a line of the input. Replace `<input>` with the text itself, verbatim.

**Voice 1 — Claude Skeptic** (Agent tool):

```text
Agent(
  subagent_type="tao:senior-skeptic-reviewer",
  model="opus",
  prompt="Review this as a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright? Be constructive but direct. Where the claim is about this codebase, ground your critique in the actual files — read them, don't reason abstractly.\n\n<input>\n\n[If --files: 'Relevant context files: <paths>']\n[If --focus-areas: 'Focus on: <areas>']\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]]. Budget 32,000 thinking tokens.']"
)
```

**Voice 2 — Grok Challenger** (Bash tool — self-contained, so it resolves its own paths rather than relying on any earlier `Bash` call's shell state):

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

## Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — <the ERROR line the script printed>. Edit config/models.json to change provider.]`. Quote the error line rather than guessing a cause.

## Present results

Show both responses as human-readable text with clear attribution, then a mechanical merge — no editorial layer, no recommendation unless the user asks for one.

```text
## Claude Opus
<claude response verbatim>

## Grok 4.3
<grok response verbatim, or "[Grok unavailable: check XAI_API_KEY in ~/.zshenv]">

## Points raised by both models
<deduplicated list of points both raised>

## Points raised by only one model
<list with attribution — potential unique insights or model-specific blind spots>

## Explicit disagreements
<only where the models took directly opposing positions — quote both sides>
```

## Run stats

Extract `[tao-stats]` lines from Bash stderr (lines starting with `[tao-stats]`). Use `—` for the Claude voice.

```text
## Run stats
| Voice   | Provider | Model        | Tokens in | Tokens out | Time   | Tok/s |
|---------|----------|--------------|-----------|------------|--------|-------|
| Claude  | claude   | opus         | —         | —          | —      | —     |
| Grok    | xai      | <model>      | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
```

If a voice was unavailable, omit its row or mark all cells `unavailable`.
