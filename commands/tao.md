---
name: tao
description: "Multi-model reasoning router with many modes"
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
| debug | `tao:debug-investigator` | opus | Systematic debugging with hypothesis-driven investigation |
| codereview | `tao:code-reviewer` | opus | Comprehensive code quality and security analysis |
| secaudit | `tao:security-auditor` | opus | Security and compliance assessment |
| analyze | `tao:architecture-analyst` | opus | Architecture and strategic code analysis (1M context) |
| planner | `tao:task-planner` | opus | Structured task planning with phases |
| think | `tao:thinker` (default) or `tao:deep-reasoner` (`--quick`) | opus | Deep reasoning, with rigorous vetting by default; `--quick` skips vetting (formerly `/tao:thinkdeep`, see standalone /tao:think command) |
| vet | 1/3/4 voices depending on depth (see below) | opus (+ external at standard/full) | Multi-perspective vetting/challenge/consensus, merged into one depth dial (see standalone /tao:vet command) |
| requirements | `tao:requirements-architect` | sonnet | Requirements discovery and technical translation |
| synthesize | `tao:perspective-synthesizer` | sonnet | Reconcile multiple viewpoints into unified strategy |
| guru-chat | 5 luminary personas + `tao:perspective-synthesizer` | sonnet personas + sonnet synthesis | Live peer-to-peer roundtable of industry luminaries, synthesized (see standalone /tao:guru-chat command) |
| refactor | `tao:refactoring-advisor` | sonnet | Code smell detection and refactoring strategy |
| precommit | `tao:precommit-validator` | sonnet | Git change validation before commit |
| docgen | `tao:doc-generator` | sonnet | Documentation generation |
| testgen | `tao:test-generator` | sonnet | Test suite generation with edge cases |
| tracer | `tao:execution-tracer` | sonnet | Code flow and dependency tracing |
| chat | `tao:chat-assistant` | sonnet | Collaborative thinking and discussion (see standalone /tao:brainstorm command) |
| clink | `tao:clink-assistant` | sonnet | External CLI integration bridging — internal use only, no standalone slash command |
| apilookup | (inline) | - | API research guidance |

`challenge`, `skeptic`, and `consensus` are no longer separate modes — they're `vet` at a fixed depth (`challenge`/`skeptic` → `--depth=standard`, `consensus` → `--depth=full`). `thinkdeep` is no longer a separate mode — it's `think --quick`. **These old names only still work via the `/tao <mode> ...` router form** (this file) — their standalone `/tao:challenge`, `/tao:skeptic`, `/tao:consensus`, and `/tao:thinkdeep` slash commands are deleted, not just deprecated. Also note: `/tao challenge` now runs its Claude voice at opus (via `tao:senior-skeptic-reviewer`), not the old sonnet-tier `tao:challenge-assessor` — slightly slower/costlier than before, since `standard` depth uses one shared Claude voice for both former challenge and skeptic framings. New usage should prefer `vet`/`think` directly.

## Argument Handling

Arguments can be passed in two ways:

1. **Natural language** (preferred): Just write what you need after the mode. Examples:
   - `/tao debug my server is crashing on startup`
   - `/tao think should we use SQLite or Postgres?`
   - `/tao vet the proposed caching strategy using Redis pub/sub` (depth chosen dynamically)
   - `/tao vet should we migrate from REST to GraphQL? --depth=full --high-effort` (force full 4-voice consensus depth)

2. **Explicit flags**: For precision or when combining multiple arguments:
   - `--high-effort` → Enable extended thinking for Claude voices (`[[ ultrathink ]]`, 32K thinking tokens) and 16K max_tokens for external API calls. Use when the decision is high-stakes or the analysis is inherently complex.
   - `--thinking` or `thinking` → Alias for `--high-effort`
   - `--files=<paths>` or `--file-paths=<paths>` → Comma-separated file/directory paths for the agent to analyze
   - `--focus-areas=<areas>` → Comma-separated areas to focus on
   - `--issue=<text>` → Bug description (debug mode)
   - `--problem=<text>` → Problem statement (think mode, with or without `--quick`)
   - `--task=<text>` → Task description (planner mode)
   - `--proposal=<text>` → Proposal/statement/question to vet (vet mode and its challenge/skeptic/consensus aliases)
   - `--depth=quick|standard|full` or `--voices=1|3|4` → Force a vet depth, skipping dynamic depth selection (vet mode only; ignored/implied for the challenge/skeptic/consensus aliases)
   - `--quick` → Skip the vetting stage (think mode only; equivalent to the old thinkdeep mode)
   - `--query=<text>` → API/library to research (apilookup mode)
   - `--prompt=<text>` → Custom prompt (chat, docgen, secaudit, tracer, clink modes)
   - `--error-logs=<text>` → Error logs (debug mode)
   - `--cli-name=<name>` → Target CLI (clink mode)

When using natural language, the entire text after the mode name is passed as the primary argument to the agent (e.g., as the issue for debug, the problem for think, the proposal/statement/question for vet and its aliases, etc.).

## Self-Contained Output Contract (ALL modes)

This contract is non-negotiable and applies to every mode below, including the synthesis step of the multi-voice modes.

Each dispatched agent runs in its own context, and the user sees ONLY the agent's final returned text — never the agent's internal chatter or the intermediate reasoning where options were generated and labeled.
All of that stays inside the agent's context, so the returned text must stand entirely on its own.

Rule (mechanical, self-checkable): any label, shorthand, or back-reference used in a conclusion — e.g. "Option A", "the second proposal", "Voice 2's position", "approach #3", "the rejected design" — MUST be defined in the same output, in a section that *precedes* the conclusion.
If internal labels were used while reasoning, restate each labeled item in full at its first user-facing mention.

Before returning, run this check: *could a reader who saw nothing but this single message understand every option, voice, or finding referenced in the conclusion?*
If not, add an "Options/Positions Considered" section that defines each one (target 20–400 words per item — err verbose; a few extra tokens beats a downstream misinterpretation) before stating the conclusion.
Never report "X is strongest, Y was rejected" without the reader having first been shown what X and Y actually are.

## Dispatch Instructions

### Standard Modes (Single Agent)

For most modes, invoke the Agent tool like this:

```text
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
5. Output format instruction — always tell the agent how to format its response for human consumption. The dedicated command files (e.g. `commands/debug.md`, `commands/codereview.md`) contain per-mode format specs; use those as the reference. Never let an agent return a raw JSON blob as its final user-facing response.

### Vet Mode (and challenge/skeptic/consensus aliases)

**Preferred invocation: `/tao:vet`** — the standalone command in `commands/vet.md` contains the full depth-dial dispatch logic (quick=1 voice, standard=3 voices, full=4 voices) and the dynamic depth-selection rule used when no depth is specified.

When `/tao vet` is invoked (mode argument rather than dedicated command): forward to the same logic in `commands/vet.md`, including its Step 0 dynamic depth decision when `--depth`/`--voices` is absent.

When `/tao challenge`, `/tao skeptic`, or `/tao consensus` is invoked (legacy mode names, kept as forwarding aliases): forward to `commands/vet.md` with the depth fixed as follows, skipping Step 0's dynamic decision:

- `challenge` → `--depth=standard`
- `skeptic` → `--depth=standard`
- `consensus` → `--depth=full`

Model assignments for all depths are in `config/models.json` under `vet.quick` / `vet.standard` / `vet.full`.

### Think Mode (and thinkdeep alias)

**Preferred invocation: `/tao:think`** — the standalone command in `commands/think.md` contains both the default (vetted) and `--quick` (unvetted) dispatch logic.

When `/tao think` is invoked (mode argument rather than dedicated command): forward to the same logic in `commands/think.md`.

When `/tao thinkdeep` is invoked (legacy mode name, kept as a forwarding alias): forward to `commands/think.md`'s `--quick` path (dispatches `tao:deep-reasoner`, no vetting stage).

### Guru-Chat Mode

**Preferred invocation: `/tao:guru-chat`** — the standalone command in `commands/guru-chat.md` contains the full roundtable logic (five luminary personas, team-based discussion with graceful fallback to parallel subagents, then synthesis via `tao:perspective-synthesizer`).

When `/tao guru-chat` is invoked (mode argument rather than dedicated command): forward to the same logic documented in `commands/guru-chat.md`.

### Inline Modes (No Agent Needed)

#### apilookup mode

Output this research guidance, then use web search tools to research the query:

```text
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

- Most modes use the Claude Max subscription (free tier) — no external cost or API tokens consumed.
- Each mode dispatches to a sub-agent that runs in its own context, so the agent's intermediate reasoning and chatter stay out of your main conversation window — only its final synthesized output returns.
- `vet` at `standard`/`full` depth (and its `challenge`/`skeptic`/`consensus` aliases) use external models with graceful degradation if unavailable; `quick` depth is Claude-only.
- Required for full multi-LLM functionality (defaults — all swappable in `config/models.json`):
  - `XAI_API_KEY` in `~/.zshenv` — xAI Grok (vet standard/full critic/challenger voice)
  - Codex plugin installed + OpenAI subscription — vet full-depth analyst voice; swap to `openai` provider if preferred
  - Ollama: `ollama pull qwen3:32b` then `ollama serve` — local voice; swap to `groq` provider for fast cloud inference without GPU
  - `OPENAI_API_KEY` in `~/.zshenv` — optional; enables `openai` provider (gpt-5 default)
  - `GROQ_API_KEY` in `~/.zshenv` — optional; enables `groq` provider (meta-llama/llama-4-scout-17b-16e-instruct default, very fast)
  - `GEMINI_API_KEY` in `~/.zshenv` — optional; enables `gemini` provider (gemini-2.5-pro default)
- Default local model is set by `"_default_local_model"` in `config/models.json` — change it there to use a different Ollama model across all modes simultaneously.
- All other model assignments are configurable in `config/models.json` — no command files need editing.
