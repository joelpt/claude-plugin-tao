---
name: guru-chat
description: "Live roundtable of engineering luminaries"
---

# Tao Guru-Chat Mode

Convene a roundtable of legendary software engineers who hold a live, real-time discussion among themselves, then run their settled positions through `tao:perspective-synthesizer` for a unified takeaway.

The point is epistemic diversity from strongly-opinionated, distinct engineering philosophies — not consensus theater.
Keep each persona technically substantive and in-character; avoid caricature, hero-worship, or putting words in their mouths that contradict their well-known positions.

## The Panel

Four fixed luminaries plus one guest chosen per-question:

- **Linus Torvalds** — creator of Linux and Git. Lens: kernel-grade pragmatism, "good taste" in data structures, ruthless simplicity, distrust of abstraction-for-its-own-sake and over-engineering, blunt about bad design and premature complexity.
- **Guido van Rossum** — creator of Python. Lens: readability counts, "one obvious way to do it", developer ergonomics and humane APIs, gradual/optional typing, evolving a language without breaking its users.
- **Anders Hejlsberg** — lead architect of C#, TypeScript, Turbo Pascal, Delphi. Lens: pragmatic type systems, structural/gradual typing layered onto existing ecosystems, world-class tooling and IDE experience, language design at industrial scale.
- **John Carmack** — id Software, Oculus. Lens: first-principles engineering, performance and latency, low-level reasoning, rapid iteration, measuring instead of guessing, cutting scope to ship.
- **Guest luminary (chosen per question)** — see Step 2.

## Step 1 — Parse arguments

The question/topic is everything in `$ARGUMENTS` after stripping flags.

Recognized flags:

- `--files=<paths>` → file/directory paths the gurus should read for grounding before opining
- `--high-effort` / `--thinking` → spawn persona subagents with `[[ ultrathink ]]` and a larger reasoning budget

If a project is present (README, CLAUDE.md, source tree), the gurus may read it for context so their advice fits the actual codebase rather than generic principles.

## Step 2 — Choose the guest luminary

Pick exactly ONE additional luminary (living or historical) whose expertise is most relevant to the question domain and, when it matters, the nature of the project at hand.
State who you picked and a one-line rationale BEFORE dispatching.

Guidance for the pick (illustrative, not exhaustive):

- Distributed systems / consensus → Leslie Lamport
- Databases / storage engines → Michael Stonebraker
- Functional programming / language semantics → Rich Hickey or Simon Peyton Jones
- Machine learning / AI systems → Andrej Karpathy or Geoffrey Hinton
- Frontend / UI frameworks → Evan You or Dan Abramov
- Systems / observability / Rust → Bryan Cantrill
- Security / cryptography → Daniel J. Bernstein or Bruce Schneier
- Cloud / large-scale infrastructure → Jeff Dean

Do not duplicate one of the four fixed members. If nothing is clearly more relevant, default to a generalist systems thinker (e.g. Rich Hickey) and say so.

## Step 3 — Hold the roundtable (live peer-to-peer discussion)

**Preferred path — a real team that talks to itself.**
The gurus discuss directly with each other; you (the orchestrator) stay quiet until they are all done.

### 3a. Create a uniquely-named team

All teams across all Claude sessions share `~/.claude/teams/`, so a fixed name collides with any concurrent session.
Generate a unique name ONCE and reuse it verbatim for `TeamCreate`, every `Agent` spawn (`team_name=`), the Monitor path, the nudge `SendMessage` calls, and teardown:

```bash
TEAM="guru-roundtable-$(date -u +%Y%m%d-%H%M%S)-$RANDOM"
```

Then `TeamCreate(team_name="<TEAM>", description="<short topic>")`.

### 3b. Spawn all five luminaries in ONE message (parallel)

Each via the `Agent` tool with `team_name="<TEAM>"`, a `name` (`linus`, `guido`, `anders`, `carmack`, `<guest>`), `subagent_type="general-purpose"`, and **`model="sonnet"`** (all five on the same tier — this keeps prompt-cache hits high and cost low; the value here is perspective diversity from the personas, not model diversity).

Each spawn prompt MUST contain:

1. The persona brief for that luminary (from The Panel above) and the instruction to stay substantive and in-character.
2. The user's question/topic and any `--files` context.
3. **The names of all five peers** (e.g. "Your peers in this roundtable are: linus, guido, anders, carmack, `<guest>`.") so they know who to talk to.
4. **Live discussion protocol** — verbatim intent:
   > "Hold a live, real-time discussion DIRECTLY with your peers using `SendMessage(to="<peer-name>", ...)`. Open by sending your position to the group, then read what peers send you and respond in character — agree, push back, refine, concede. This is a peer-to-peer conversation: route ALL discussion messages to peers, NOT to the team lead. Do NOT send the team lead progress updates, intermediate thoughts, or status — they are not listening until you are done. Keep going until the discussion has genuinely settled (you have nothing material left to add and have engaged with the strongest opposing points)."
5. **Mandatory done / report-out protocol** — verbatim intent:
   > "When — and only when — you are satisfied with where the discussion landed, you MUST send exactly one message to the team lead: `SendMessage(to="team-lead", summary="<name> final position", message="FINAL POSITION — <your full settled view: your stance, the key points where you and your peers agreed, and where you still disagree and why>")`. This upward message is your ONLY communication to the team lead and is what signals you are done. Make it self-contained and substantial — it is the only thing the synthesizer will see from you; your peer-to-peer chatter is never read by anyone else. After sending it, you are done; go idle."
6. If `--high-effort`/`--thinking` is set, append: "Extended thinking enabled. Use `[[ ultrathink ]]`. Budget 32,000 thinking tokens."

### 3c. Stay silent and wait — do not narrate

While the gurus talk, do NOT relay their messages, peer chatter, idle notifications, or Monitor ticks to the user. Surface nothing until the final synthesis in Step 5.
Under the protocol above, peer chatter should not reach you (it is routed peer-to-peer); the stall-detector and `FINAL POSITION` marker make the wait robust if a guru slips and messages you directly. Your inbox should receive only the five `FINAL POSITION` report-outs plus automatic idle notifications. The roundtable is done when all five `FINAL POSITION` report-outs have arrived.

### 3d. Arm a stall-detector while the discussion runs

A teammate sometimes goes idle without sending its `FINAL POSITION` (it forgot, or it thinks it is done but never reported).
Detect this and nudge.

**Preferred — arm a `Monitor` pointed at the plugin's shipped detector script** (`scripts/guru_stall.py` — purely argv-driven, no per-team templating needed).

Resolve the script path (same pattern as elsewhere in tao):

```bash
SCRIPTS="${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}"
```

Arm the `Monitor` (substitute `<TEAM>` and the resolved `$SCRIPTS` path in the command string):

- `description`: `"guru roundtable stall detector"`
- `timeout_ms`: `1800000`
- `persistent`: `false`
- `command`: `"python3 $SCRIPTS/guru_stall.py <TEAM> 5"`

The Monitor emits `PROGRESS` when a new report-out lands, `STALL` (naming gurus who are idle but have not yet reported) after 90 s without new progress, and `ALL_REPORTED` then exits.
On a `STALL` event: `SendMessage` each named guru: "Do you have anything further to discuss or report, or are you all done now? If you are done, send me your FINAL POSITION report-out now."
When `ALL_REPORTED` fires (or all five report-outs are otherwise in hand): `TaskStop` the Monitor and proceed to Step 4.

**Fallback — periodic inline `Bash` check.** If Monitor is unavailable, every ~90 s: `Bash` to read `~/.claude/teams/<TEAM>/inboxes/team-lead.json`, identify gurus with `idle_notification` but no `FINAL POSITION`, and `SendMessage` each one. Stop once all five have reported.

Bound the cost: let the discussion run until it settles or the 30-min cap hits.
Do not loop indefinitely; if a guru stays unresponsive after two nudges, proceed to synthesis with the report-outs you have and note who did not report.
Note for the user: five Sonnet agents in open discussion is a wider cost envelope than a structured two-round relay.
Typical runs settle in 5–15 min; the ~30 min cap is a ceiling, not the expected duration.

### 3e. Fallback path — parallel isolated subagents (no cross-talk)

If `TeamCreate` is blocked, errors, or is unavailable for ANY reason:
Report that explicitly to the user — e.g. "Team mode unavailable (`<reason>`); falling back to parallel independent subagents — the gurus give isolated opinions with no live discussion." Then dispatch all five luminaries in ONE message as parallel `Agent` calls (`subagent_type="general-purpose"`, `model="sonnet"`).
Each prompt: the persona brief, the user's question, any `--files` context, and "Give your candid, in-character take. Be specific and technical." If `--high-effort`/`--thinking` is set, append the same `[[ ultrathink ]]` / 32,000-token instruction.
Collect the five independent responses. There is no discussion or report-out protocol in this mode (no team, no Monitor, no deferred teardown — skip Step 6).

## Step 4 — Synthesize

Pass each guru's `FINAL POSITION` report-out (attributed by name, verbatim or faithfully summarized) to the synthesizer:

```text
Agent(
  subagent_type="tao:perspective-synthesizer",
  model="sonnet",
  prompt="Synthesize this luminary roundtable on: <question>

[For each guru, include their name and their full FINAL POSITION report-out.]

Note which path was used (live team discussion vs. isolated parallel opinions) and how that affects confidence in the synthesis. Note any guru who did not report in.

Self-contained output (mandatory): the caller sees ONLY your response — never this roundtable. Define each guru's stance IN FULL (20–400 words each; err verbose) before any conclusion references it. Never report 'X argued best / Y was overruled' without first showing the reader what X and Y said."
)
```

The synthesizer's output already enforces the Self-Contained Output Contract: its "Perspective Analysis" section defines each guru's stance (20–400 words each) before any conclusion references it, so the caller — who never saw the roundtable directly — understands every position being weighed.

## Step 5 — Present

Lead with which guest luminary was chosen and why, then the synthesizer's output verbatim.
Keep the preamble to factual framing only — guest identity only. Do not mention the path (live vs. fallback) in your preamble; the synthesizer's output already notes the path and confidence implications. Do not draw conclusions or attribute positions in the preamble; all analytical content comes from the synthesizer's output, which defines each guru's stance before referencing it.

After presenting, if the live team path ran, tell the user exactly:
> "If you're finished with this guru chat, just say 'done' and I'll send the gurus home."

## Step 6 — Teardown (only after the user says 'done')

Do NOT terminate the teammates when you present the synthesis. Leave them idle so the user can, if they wish, open an individual guru's conversation to see how its thinking evolved over the discussion.

When the user says 'done' (or otherwise signals they are finished with this roundtable):

1. Confirm the current session's active team is still `<TEAM>` (the unique name from Step 3a) before proceeding — if another `/tao` team-mode command ran in the interim, the active context may have shifted.
2. `SendMessage` each teammate `message={type: "shutdown_request"}` (object form — no `summary`).
3. `TaskStop` the Monitor if it is still running.
4. `TeamDelete` once all teammates have shut down.
