# Vet — Full depth (3 voices — Claude advocate + Grok critic + Codex/GPT analyst, synthesized)

Dispatch all three in ONE message (parallel tool calls).

**Passing the input to a Bash voice.** Give the text to `llm_call.py` through a *quoted heredoc* whose delimiter is a fresh random token you invent for each call (for example `TAO_7QK2M9_EOF`), never a fixed literal. A double-quoted shell string would execute backticks and `$(...)` inside the vetted text, and a fixed delimiter can collide with a line of the input. Replace `<input>` with the text itself, verbatim.

**Voice 1 — Claude Advocate** (Agent tool):

```text
Agent(
  subagent_type="tao:consensus-advocate",
  model="opus",
  prompt="Argue FOR this decision. Make the strongest possible case for proceeding.\n\n<input>\n\n[If --files: 'Relevant context files: <paths>']\n[If --focus-areas: 'Focus on: <areas>']\n[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for analysis.']"
)
```

**Voice 2 — Grok Critic** (Bash tool — self-contained; this is a separate tool call from the other voices, so it resolves its own paths rather than relying on any earlier `Bash` call's shell state):

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"
SCRIPTS="$PLUGIN_ROOT/scripts"
CONFIG="$PLUGIN_ROOT/config/models.json"
python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.full.critic \
  --system="Argue AGAINST this decision. Find flaws, risks, hidden costs, and failure modes. Be direct." \
  --max-tokens=<4096 standard | 16384 high-effort> <<'TAO_RANDOM_EOF'
<input>
TAO_RANDOM_EOF
```

**Voice 3 — Codex/GPT Analyst** (Bash tool — self-contained, same reason):

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"
SCRIPTS="$PLUGIN_ROOT/scripts"
CONFIG="$PLUGIN_ROOT/config/models.json"
python3 "$SCRIPTS/llm_call.py" \
  --config "$CONFIG" --role=vet.full.analyst \
  --system="Provide neutral, balanced analysis of this decision. Weigh evidence objectively without advocacy." \
  --max-tokens=<4096 standard | 16384 high-effort> <<'TAO_RANDOM_EOF'
<input>
TAO_RANDOM_EOF
```

Then synthesize:

```text
Agent(
  subagent_type="tao:consensus-synthesizer",
  model="opus",
  prompt="""Synthesize 3 perspectives on: <input>

## Claude Advocate (Claude Opus)
<advocate_response>

## Grok Critic (Grok 4.3)
<grok_response_or_unavailable>

## Codex/GPT Analyst
<codex_response_or_unavailable>

Note any unavailable voices and how that affects confidence.

Self-contained output (mandatory): the caller sees ONLY your response — never these three raw voices. Open with a 'Positions Considered' section defining each distinct option/stance the voices argued (20–400 words each; err verbose) before any recommendation references it. Never report 'option X is strongest / Y was rejected' without first showing the reader what X and Y are."""
)
```

## Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — <the ERROR line the script printed>. Edit config/models.json to change provider.]`. Quote the error line rather than guessing a cause.

## Run stats

Append after the synthesizer returns. `—` for Claude voices (no token telemetry available from Agent calls).

```text
## Run stats
| Voice         | Provider | Model         | Tokens in | Tokens out | Time   | Tok/s |
|---------------|----------|---------------|-----------|------------|--------|-------|
| Claude Opus   | claude   | opus          | —         | —          | —      | —     |
| Grok Critic   | xai      | <model>       | <tok_in>  | <tok_out>  | <Xs>   | <N>   |
| Codex Analyst | codex    | <model>       | ?         | ?          | <Xs>   | n/a   |
```

Omit rows for unavailable voices or mark all cells `unavailable`.
