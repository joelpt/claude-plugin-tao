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

All modes are available as `/tao <mode> <args>`; most also have a dedicated `/tao:<mode> <args>` command. `chat` is exposed as `/tao:brainstorm`. `clink` has no standalone command — it's internal-only, reachable via `/tao clink` (used by tao/Claude for CLI-bridging guidance).

`/tao:vet` and `/tao:think` each merge what used to be several separate commands (see below) — the old mode names (`challenge`, `skeptic`, `consensus`, `thinkdeep`) still work as `/tao <mode>` forwarding aliases, but have no standalone `/tao:<mode>` command anymore.

### Claude-only modes (free via Claude Max)

| Mode | Model | Description |
|------|-------|-------------|
| `debug` | Opus | Hypothesis-driven root-cause investigation |
| `codereview` | Opus | Severity-ranked code quality and security review |
| `secaudit` | Opus | OWASP-aligned security and compliance audit |
| `analyze` | Opus | Architecture and technical debt analysis |
| `planner` | Opus | Phased task planning with milestones |
| `think` | Opus | Deep reasoning; vets its own answer by default, `--quick` skips vetting (formerly also `thinkdeep`) |
| `requirements` | Sonnet | Business requirements → technical specifications |
| `synthesize` | Sonnet | Reconcile competing viewpoints into a unified strategy |
| `refactor` | Sonnet | Code smell detection and refactoring plan |
| `precommit` | Sonnet | Pre-commit validation with go/no-go verdict |
| `docgen` | Sonnet | API docs, architecture docs, inline docstrings |
| `testgen` | Sonnet | Test suite with edge case analysis |
| `tracer` | Sonnet | Execution flow and dependency tracing |
| `chat` (see `/tao:brainstorm`) | Sonnet | Collaborative discussion and brainstorming |
| `clink` (internal only, no standalone command) | Sonnet | CLI integration and bridging guidance |
| `apilookup` | — | API/library quick-reference research |
| `guru-chat` | Sonnet ×5 + Sonnet | Live roundtable of luminaries (Linus, Guido, Hejlsberg, Carmack + a question-relevant guest) who discuss peer-to-peer, then synthesized |

### Vet mode (variable voices — merges former vet/challenge/skeptic/consensus)

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
/tao debug my API returns 500 on POST /users but only in production
/tao codereview --files=src/auth --focus-areas=security
/tao think should we use PostgreSQL or DynamoDB for user sessions?
/tao vet should we migrate from REST to GraphQL? --depth=full --high-effort
/tao vet we don't need integration tests for this module
/tao vet the proposed caching strategy using Redis pub/sub
/tao guru-chat should this codebase adopt a plugin architecture or stay monolithic?
```

Pass `--high-effort` to any mode for extended thinking (Claude) and 16K token budgets (external APIs).

## Layout

```text
.claude-plugin/plugin.json   ← manifest (name, version, description)
commands/                    ← slash command definitions (one per mode)
agents/                      ← subagent definitions (dispatched by commands)
scripts/llm_call.py          ← multi-provider LLM caller (Grok, OpenAI, Groq, Gemini, Ollama, Codex)
config/models.json           ← model assignments per role (edit to swap providers)
```

Distributed via the [`joelpt-claude-plugins`](https://github.com/joelpt/joelpt-claude-plugins) marketplace.
Bump `.claude-plugin/plugin.json` `version` (CalVer, minimum patch) on any change — the marketplace cache is keyed by version.

## License

MIT. See `LICENSE`.
