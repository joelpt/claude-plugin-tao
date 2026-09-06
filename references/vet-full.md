# Vet — Full depth (4 voices — Claude advocate + Grok critic + Codex/GPT analyst + Ollama, synthesized)

Dispatch all four in ONE message (parallel tool calls).

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

## Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — check API key or Ollama. Edit config/models.json to change provider.]`

## Run stats

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
