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

1. **guru-chat live roundtables (done, #1)** — peer-to-peer teammate discussion on the current Agent Teams model: named agents plus `SendMessage`, one implicit team per session, and lead-driven rounds (open, rebuttal, final) so a teammate cannot finalize before engaging a peer. A stall detector (`scripts/guru_stall.py`) counts only conforming finals. A small live trial confirmed peers read each other's messages and change positions between rounds.
2. **guru-chat stats report (done)** — a per-teammate table of tokens, messages sent and received, wall-clock time and a 1-5 contribution score, computed by `scripts/guru_stats.py` from the teammates' own transcripts.
3. **Domain-adaptive panels (done, #4; subsumes #3)** — the lead chooses the panel for every question. The four software luminaries plus a domain guest are only a suggested default for software questions; other topics get figures suited to the subject, with lens diversity and at least one dissenter, and `--panel=<names>` forces an exact panel. There is no `auto` mode. Panelists are explicitly simulated lenses grounded in public work, never presented as authentic quotations.

Add milestones here, and adopt the milestone/epic/DAG structure from the sync-plan standard, once roughly five or more items are open.

## Lessons

- Reference-file loading broke silently across vet/think/guru-chat once (fixed in 17574e4); reference paths need a test, not just a read.
- A multi-agent protocol is only proven by running it. Unit tests of the stall detector passed while the real question, whether teammates read each other before finalizing, was untested until a live trial.
- Teammate transcripts (`subagents/agent-*.jsonl`, keyed by session id) are the reliable source for per-agent stats. Streaming repeats one message's usage across several rows, so deduplicate by message id.
- Platform features this plugin leans on (Agent Teams, `TeamCreate`, `team_name`) change between Claude Code releases; verify against the running version before building on them.
