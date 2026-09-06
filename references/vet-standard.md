# Vet — Standard depth (3 voices — Claude + Grok + Ollama)

Dispatch all three in ONE message (parallel tool calls).

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

## Handle results

For any Bash call that exits non-zero: substitute `[Voice unavailable — check API key or Ollama. Edit config/models.json to change provider.]`

## Present results

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

## Run stats

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
