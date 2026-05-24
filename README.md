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

All modes are available as `/tao <mode> <args>` or as dedicated `/tao:<mode> <args>` commands.

### Claude-only modes (free via Claude Max)

| Mode | Model | Description |
|------|-------|-------------|
| `thinkdeep` | Opus | Multi-stage deep reasoning for complex problems |
| `debug` | Opus | Hypothesis-driven root-cause investigation |
| `codereview` | Opus | Severity-ranked code quality and security review |
| `secaudit` | Opus | OWASP-aligned security and compliance audit |
| `analyze` | Opus | Architecture and technical debt analysis |
| `planner` | Opus | Phased task planning with milestones |
| `think` | Opus | Deep reasoning + automatic vetting via sub-agents |
| `vet` | Opus | Multi-perspective proposal vetting |
| `requirements` | Sonnet | Business requirements → technical specifications |
| `synthesize` | Sonnet | Reconcile competing viewpoints into a unified strategy |
| `refactor` | Sonnet | Code smell detection and refactoring plan |
| `precommit` | Sonnet | Pre-commit validation with go/no-go verdict |
| `docgen` | Sonnet | API docs, architecture docs, inline docstrings |
| `testgen` | Sonnet | Test suite with edge case analysis |
| `tracer` | Sonnet | Execution flow and dependency tracing |
| `chat` | Sonnet | Collaborative discussion and brainstorming |
| `clink` | Sonnet | CLI integration and bridging guidance |
| `apilookup` | — | API/library quick-reference research |

### Multi-LLM modes (external voices)

| Mode | Voices | Description |
|------|--------|-------------|
| `consensus` | Claude Opus + Grok 4.3 + Codex/GPT + Ollama | 4-voice parallel decision analysis |
| `challenge` | Claude Sonnet + Grok 4.3 + Ollama | 3-voice adversarial statement challenge |
| `skeptic` | Claude Opus + Grok 4.3 + Ollama | 3-voice constructive proposal skepticism |

Multi-LLM modes degrade gracefully — if an external voice is unavailable, tao notes it and continues with the remaining voices.

## Setup for multi-LLM modes

```bash
# xAI Grok (consensus critic, challenge/skeptic challenger)
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
/tao consensus should we migrate from REST to GraphQL? --high-effort
/tao challenge we don't need integration tests for this module
/tao vet the proposed caching strategy using Redis pub/sub
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
