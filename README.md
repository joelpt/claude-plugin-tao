# tao

Advanced multi-model AI reasoning workflows for Claude Code.
Routes each mode to the optimal Claude tier (Opus / Sonnet / Haiku) and adds external LLM voices for consensus and adversarial analysis.

## Install

```bash
claude plugin marketplace add joelpt/joelpt-claude-plugins
claude plugin install tao@joelpt-claude-plugins
```

Then restart Claude Code.
Requires read access to the private marketplace repo (`gh auth login`).

## Modes

Every mode is a dedicated `/tao:<mode> <args>` command — there is no bare `/tao` router command (removed: it only duplicated what each dedicated command already does standalone, at the cost of extra tokens per turn for anyone who used it).

### Claude-only modes (free via Claude Max)

| Mode | Model | Description |
|------|-------|-------------|
| `/tao:debug` | Opus | Hypothesis-driven root-cause investigation |
| `/tao:codereview` | Opus | Severity-ranked code quality and security review |
| `/tao:secaudit` | Opus | OWASP-aligned security and compliance audit |
| `/tao:analyze` | Opus | Architecture and technical debt analysis |
| `/tao:planner` | Opus | Phased task planning with milestones |
| `/tao:think` | Opus | Deep reasoning; vets its own answer by default, `--quick` skips vetting |
| `/tao:requirements` | Sonnet | Business requirements → technical specifications |
| `/tao:synthesize` | Sonnet | Reconcile competing viewpoints into a unified strategy |
| `/tao:refactor` | Sonnet | Code smell detection and refactoring plan |
| `/tao:precommit` | Sonnet | Pre-commit validation with go/no-go verdict |
| `/tao:docgen` | Sonnet | API docs, architecture docs, inline docstrings |
| `/tao:testgen` | Sonnet | Test suite with edge case analysis |
| `/tao:tracer` | Sonnet | Execution flow and dependency tracing |
| `/tao:brainstorm` | Sonnet | Collaborative discussion and brainstorming |
| `/tao:apilookup` | — | API/library quick-reference research |
| `/tao:guru-chat` | Sonnet ×5 + Sonnet | Live roundtable of luminaries (Linus, Guido, Hejlsberg, Carmack + a question-relevant guest) who discuss peer-to-peer, then synthesized |

### Vet mode (variable voices)

`/tao:vet` stress-tests a proposal, statement, or decision. Depth picks the voice count:

| Depth | Voices | Formerly | When |
|------|--------|----------|------|
| `quick` | 1 — Claude Opus | `vet` | Narrow, low-stakes, easily reversible |
| `standard` | 3 — Claude Opus + Grok 4.3 + Ollama | `challenge`, `skeptic` | Most real vetting requests — architecture/design choices, real-but-recoverable cost if wrong |
| `full` | 4 — Claude advocate + Grok critic + Codex/GPT analyst + Ollama, synthesized | `consensus` | High-stakes, hard-to-reverse, or the user explicitly wants multiple independent opinions |

Pass `--depth=quick|standard|full` (or `--voices=1|3|4`) to force a depth; **omit it and tao decides dynamically** based on the stakes and phrasing of what you're asking it to vet. Multi-voice depths degrade gracefully — if an external voice is unavailable, tao notes it and continues with the remaining voices.

## Setup for multi-LLM modes

```bash
# xAI Grok (vet standard/full critic/challenger voice)
echo 'export XAI_API_KEY=<your-key>' >> ~/.zshenv

# OpenAI direct (alternative to Codex CLI for GPT analyst voice)
echo 'export OPENAI_API_KEY=<your-key>' >> ~/.zshenv

# Groq LPU inference (very fast; alternative to Ollama for local-fast voice)
echo 'export GROQ_API_KEY=<your-key>' >> ~/.zshenv

# Ollama local voice
ollama pull qwen3:32b && ollama serve

# Codex/GPT analyst voice (OpenAI subscription, no per-token cost)
claude plugin install codex@openai-codex
```

Model assignments and the default Ollama model are configurable in `config/models.json`.

## Usage examples

```text
/tao:debug my API returns 500 on POST /users but only in production
/tao:codereview --files=src/auth --focus-areas=security
/tao:think should we use PostgreSQL or DynamoDB for user sessions?
/tao:vet should we migrate from REST to GraphQL? --depth=full --high-effort
/tao:vet we don't need integration tests for this module
/tao:vet the proposed caching strategy using Redis pub/sub
/tao:guru-chat should this codebase adopt a plugin architecture or stay monolithic?
```

Pass `--high-effort` to any mode for extended thinking (Claude) and 16K token budgets (external APIs).

## Layout

```text
.claude-plugin/plugin.json   ← manifest (name, version, description)
commands/                    ← slash command definitions (one per mode)
agents/                      ← subagent definitions (dispatched by commands)
references/                  ← dispatch templates read on demand (vet depths, think variants, guru-chat's rare branches) — cuts per-invocation token cost vs. inlining everything
scripts/llm_call.py          ← multi-provider LLM caller (Grok, OpenAI, Groq, Gemini, Ollama, Codex)
scripts/guru_stall.py        ← guru-chat's team stall detector
config/models.json           ← model assignments per role (edit to swap providers)
```

Path resolution across commands defaults to `$HOME/code/claude-plugin-tao`; override with `TAO_PLUGIN_ROOT` (or the legacy `TAO_SCRIPTS`, which still works — the plugin root is derived from its parent) if installed elsewhere.

Distributed via the [`joelpt-claude-plugins`](https://github.com/joelpt/joelpt-claude-plugins) marketplace.
Bump `.claude-plugin/plugin.json` `version` (CalVer, minimum patch) on any change — the marketplace cache is keyed by version.

## License

MIT. See `LICENSE`.
