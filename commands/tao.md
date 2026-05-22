---
name: tao
description: "Advanced reasoning workflows routing to optimal Claude model tiers (Opus/Sonnet/Haiku) plus external LLMs (Grok 4.3, Codex/GPT, Ollama qwen3:32b) for consensus and adversarial modes. Usage: /tao <mode> [args]. Modes: thinkdeep, debug, codereview, secaudit, analyze, planner, think, vet, challenge, skeptic, requirements, synthesize, consensus, refactor, precommit, docgen, testgen, tracer, chat, clink, apilookup"
context: fork
---

# Tao - Advanced Reasoning Workflows

Multi-model reasoning workflows that route to optimal Claude model tiers (Opus/Sonnet/Haiku) for most task types, with external LLM voices added for consensus and adversarial analysis where epistemic diversity matters most.

## Script Path Resolution

External LLM calls use `scripts/llm_call.py` and read model assignments from `config/models.json`. Resolve paths at invocation time:

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

If `TAO_SCRIPTS` is not set, falls back to the default dev location. Users with a non-standard install should set `TAO_SCRIPTS` in `~/.zshenv`.

Graceful degradation: if a Bash call to `llm_call.py` exits non-zero, treat that voice as unavailable and note it in output. Never abort the entire tao invocation because one external voice failed.

## Mode Routing

When the user invokes `/tao <mode>`, dispatch to the appropriate agent or handler:

| Mode | Agent | Model | Description |
|------|-------|-------|-------------|
| thinkdeep | `tao:deep-reasoner` | opus | Deep reasoning for complex problems |
| debug | `tao:debug-investigator` | opus | Systematic debugging with hypothesis-driven investigation |
| codereview | `tao:code-reviewer` | opus | Comprehensive code quality and security analysis |
| secaudit | `tao:security-auditor` | opus | Security and compliance assessment |
| analyze | `tao:architecture-analyst` | opus | Architecture and strategic code analysis (1M context) |
| planner | `tao:task-planner` | opus | Structured task planning with phases |
| think | `tao:thinker` | opus | Deep reasoning with rigorous vetting via sub-agents |
| vet | `tao:proposal-vetting-judge` | opus | Multi-perspective proposal vetting and validation |
| challenge | `tao:challenge-assessor` + Grok | sonnet + external | Evidence-based challenge + adversarial external voice |
| skeptic | `tao:senior-skeptic-reviewer` + Grok | opus + external | Constructive skepticism + sharp external critic |
| requirements | `tao:requirements-architect` | sonnet | Requirements discovery and technical translation |
| synthesize | `tao:perspective-synthesizer` | sonnet | Reconcile multiple viewpoints into unified strategy |
| consensus | Claude + Grok + Codex + Ollama | opus + 3 external | 4-voice multi-LLM decision analysis (see /tao:consensus) |
| refactor | `tao:refactoring-advisor` | sonnet | Code smell detection and refactoring strategy |
| precommit | `tao:precommit-validator` | sonnet | Git change validation before commit |
| docgen | `tao:doc-generator` | sonnet | Documentation generation |
| testgen | `tao:test-generator` | sonnet | Test suite generation with edge cases |
| tracer | `tao:execution-tracer` | sonnet | Code flow and dependency tracing |
| chat | `tao:chat-assistant` | sonnet | Collaborative thinking and discussion |
| clink | `tao:clink-assistant` | sonnet | External CLI integration bridging |
| apilookup | (inline) | - | API research guidance |

## Argument Handling

Arguments can be passed in two ways:

1. **Natural language** (preferred): Just write what you need after the mode. Examples:
   - `/tao debug my server is crashing on startup`
   - `/tao challenge we don't need integration tests for this module`
   - `/tao think should we use SQLite or Postgres?`
   - `/tao vet the proposed caching strategy using Redis pub/sub`
   - `/tao consensus should we migrate from REST to GraphQL? --high-effort`

2. **Explicit flags**: For precision or when combining multiple arguments:
   - `--high-effort` → Enable extended thinking for Claude voices (`[[ ultrathink ]]`, 32K thinking tokens) and 16K max_tokens for external API calls. Use when the decision is high-stakes or the analysis is inherently complex.
   - `--thinking` or `thinking` → Alias for `--high-effort`
   - `--files=<paths>` or `--file-paths=<paths>` → Comma-separated file/directory paths for the agent to analyze
   - `--focus-areas=<areas>` → Comma-separated areas to focus on
   - `--question=<text>` → Decision question (consensus mode)
   - `--issue=<text>` → Bug description (debug mode)
   - `--problem=<text>` → Problem statement (thinkdeep, think modes)
   - `--task=<text>` → Task description (planner mode)
   - `--statement=<text>` → Statement to challenge (challenge mode)
   - `--proposal=<text>` → Proposal to vet (vet mode)
   - `--query=<text>` → API/library to research (apilookup mode)
   - `--prompt=<text>` → Custom prompt (chat, docgen, secaudit, tracer, clink modes)
   - `--error-logs=<text>` → Error logs (debug mode)
   - `--cli-name=<name>` → Target CLI (clink mode)

When using natural language, the entire text after the mode name is passed as the primary argument to the agent (e.g., as the issue for debug, statement for challenge, problem for think/thinkdeep, proposal for vet, etc.).

## Dispatch Instructions

### Standard Modes (Single Agent)

For most modes, invoke the Agent tool like this:

```
Agent(
  subagent_type="tao:<agent-name>",
  model="<model-tier>",
  prompt="<compiled prompt with all arguments and context>"
)
```

Include in the agent prompt:
1. The mode-specific arguments (issue, problem, files, etc.)
2. Whether high-effort/thinking mode is enabled (add ultrathink instruction if so)
3. Any file paths the agent should read using Read/Grep tools
4. The focus areas if specified

### Consensus Mode

**Preferred invocation: `/tao:consensus`** — the standalone command in `commands/consensus.md` contains the full 4-voice parallel dispatch logic (Claude Opus advocate + Grok 4.3 critic + Codex/GPT analyst + Ollama local).

When `/tao consensus` is invoked (mode argument rather than dedicated command): forward to the same logic. Resolve paths and dispatch as documented in `commands/consensus.md`. Model assignments are in `config/models.json`.

### Challenge and Skeptic Modes (Claude + Grok Parallel)

Both modes run Claude and Grok 4.3 in parallel for dual-perspective challenge analysis.

**Resolve paths**:
```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
CONFIG="$SCRIPTS/../config/models.json"
```

**Dispatch 2 voices in ONE message** (parallel tool calls):

For **challenge** mode:
- Claude (Agent): `Agent(subagent_type="tao:challenge-assessor", model="sonnet", prompt="Challenge this: <statement>")`
- Grok (Bash): `printf '%s\n' "<statement>" | python3 "$SCRIPTS/llm_call.py" --config "$CONFIG" --role=challenge.challenger --system="Challenge this statement aggressively. Find every flaw, assumption, and risk. Be direct." --max-tokens=4096`

For **skeptic** mode:
- Claude (Agent): `Agent(subagent_type="tao:senior-skeptic-reviewer", model="opus", prompt="Review skeptically: <proposal>")`
- Grok (Bash): `printf '%s\n' "<proposal>" | python3 "$SCRIPTS/llm_call.py" --config "$CONFIG" --role=skeptic.challenger --system="Be a sharp senior skeptic. What could go wrong? What assumptions are wrong? What would you reject outright?" --max-tokens=4096`

**After both complete**, present results with clear attribution:

```
## Claude's Analysis
<claude response>

## Grok's Challenger Take
<grok response, or "[Grok unavailable: check XAI_API_KEY in ~/.zshenv]">

## Where They Agree
<synthesize convergence points>

## Where They Diverge
<synthesize key disagreements and what that tells us>
```

### Inline Modes (No Agent Needed)

#### apilookup mode
Output this research guidance, then use web search tools to research the query:

```
RESEARCH GUIDANCE for: <query>

1. Identify official documentation site
2. Verify current version and check for breaking changes
3. Search for: "[query] official documentation", "[query] latest examples [current-year]"
4. Locate: installation, quick start, API reference, common patterns
5. Capture: core concepts, key functions, auth requirements, common pitfalls
```

Then use WebSearch/WebFetch to actually look up the information.

## Extended Thinking / High Effort

When `--high-effort` (or `--thinking`) is specified:

- **Claude agents**: Add to the agent prompt: "Extended thinking is enabled. Use `[[ ultrathink ]]` for each analysis step. Budget 32,000 thinking tokens per step for thorough reasoning."
- **External API calls**: Use `--max-tokens=16384` instead of the default 4096.
- **When to auto-apply high effort**: Only when the user explicitly requests it. The calling context knows the stakes better than tao does.

## Notes

- Most modes use Claude Max (free tier) — no external cost or keys needed.
- Consensus, challenge, and skeptic modes use external models with graceful degradation if unavailable.
- Required for full multi-LLM functionality:
  - `XAI_API_KEY` in `~/.zshenv` — xAI Grok (consensus critic + challenge/skeptic challenger)
  - Codex plugin installed + OpenAI subscription — consensus analyst voice
  - Ollama: `ollama pull qwen3:32b` then `ollama serve` — consensus local voice
- Model assignments are configurable in `config/models.json` — edit that file to swap providers without touching command files.
- All agents have access to Read, Grep, Glob, Bash, and other Claude Code tools.
- `context: fork` in this file's frontmatter isolates the entire tao run in a fresh subcontext — intermediate agent chatter doesn't accumulate in your main conversation.
