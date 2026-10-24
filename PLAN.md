> **Live status & DAG: tracking issue [#2](https://github.com/joelpt/claude-plugin-tao/issues/2)**

# tao — design and rationale

tao is a Claude Code plugin of reasoning workflows. Each mode is a dedicated `/tao:<mode>` command that routes to the cheapest Claude tier adequate for the job (Opus / Sonnet / Haiku) and, for vetting, can add external LLM voices.

## Design tenets

- **One command per mode, no router.** A bare `/tao` router only duplicated the dedicated commands and cost tokens every turn, so it was removed.
- **Model tier follows task difficulty.** Opus for debugging, review, security, analysis, planning and deep reasoning; Sonnet for the structured-output modes. Tiers live in `config/models.json`.
- **Vet depth scales with stakes.** `quick` (1 voice), `standard` (2), `full` (3, synthesized). With no flag, tao picks the depth from the phrasing and stakes of the request.
- **Degrade gracefully.** If an external voice (Grok via xAI, GPT via Codex or OpenAI) is unavailable, tao notes it and continues with the remaining voices.
- **Reference files are loaded on demand.** Per-mode procedure lives in `references/` and is read only when that mode runs, keeping command prompts small.
- **No local-model voice.** An Ollama / LM Studio voice was tried and removed; external voices go through `scripts/llm_call.py` and `scripts/models.py`.

## Layout

- `commands/` — slash commands (one per mode).
- `agents/` — subagents the commands dispatch to by name.
- `references/` — per-mode procedure files (vet depths, think, guru-chat fallback and teardown).
- `config/models.json` — model routing.
- `scripts/` — external-LLM calls and the guru-chat stall detector.
- `tests/` — plugin tests.

## Roadmap (design intent)

1. **guru-chat live roundtables** — restore peer-to-peer teammate discussion on the current Agent Teams model (named agents plus `SendMessage`, one implicit team per session) and enforce multi-round deliberation. Details and verified findings are in #1.

Add milestones here, and adopt the milestone/epic/DAG structure from the sync-plan standard, once roughly five or more items are open.

## Lessons

- Reference-file loading broke silently across vet/think/guru-chat once (fixed in 17574e4); reference paths need a test, not just a read.
- Platform features this plugin leans on (Agent Teams, `TeamCreate`, `team_name`) change between Claude Code releases; verify against the running version before building on them.
