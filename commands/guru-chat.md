---
name: guru-chat
description: "Live roundtable of engineering luminaries"
---

# Tao Guru-Chat Mode

Convene a roundtable of legendary software engineers who hold a live, round-by-round discussion among themselves, then run their settled positions through `tao:perspective-synthesizer` for a unified takeaway.

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

## Step 3 — Hold the roundtable (lead-driven rounds over live peer messaging)

**Note:** shell variables do not persist across separate tool calls, so 3a, 3d, 3e, and Step 6 each resolve what they need inline.

**Preferred path — named teammates that message each other, with YOU driving explicit rounds.**
A teammate's turn ends when it stops calling tools, and peer messages are only delivered between turns. Teammates therefore cannot be trusted to self-pace a discussion: left alone they post an opening position, declare themselves "satisfied", and finalize before any reply arrives. The lead owns the round structure.

There is no team to create: the session has one implicit team, and an `Agent` call with a `name` makes that teammate addressable by `SendMessage`. Do not call `TeamCreate` or pass `team_name`.

### 3a. Generate an invocation id and the roster

Generate an id ONCE, print it, and reuse that literal value everywhere `<INV>` appears below:

```bash
INV="gc-$(date -u +%H%M%S)$RANDOM"; echo "$INV"
```

Teammate names are `<INV>-linus`, `<INV>-guido`, `<INV>-anders`, `<INV>-carmack`, `<INV>-<guest>` (the roster). The prefix keeps a second roundtable in the same session, or any unrelated teammate, from being mixed up with this one.

The lead's address is `team-lead` (the verified address). Do not use `main`: it has been rejected for teammates.

### 3b. Spawn all five luminaries in ONE message (parallel)

Each via the `Agent` tool with `name="<INV>-<luminary>"`, `subagent_type="general-purpose"`, and **`model="sonnet"`** (all five on the same tier — the value here is perspective diversity from the personas, not model diversity). If a named spawn itself errors, go to 3e and state the real error; never fall back because of a keyword search for a missing tool.

Each spawn prompt MUST contain:

1. The persona brief for that luminary (from The Panel above) and the instruction to stay substantive and in-character.
2. The user's question/topic and any `--files` context.
3. The full roster of peer names (exact `<INV>-...` names) and the invocation id.
4. The round protocol, verbatim intent:
   > "This roundtable is run in rounds by the lead. Every message you send MUST begin with the header `[RT:<INV>|<TYPE>|r<N>]` (TYPE is OPEN, REBUT or FINAL; N is the round number the lead gave you). Round 1: send your opening position to ALL peers with `SendMessage(to=\"<peer>\")`, then END YOUR TURN and do nothing else. Messages from peers are only delivered after your turn ends, so do not wait inside a turn and do not finalize now. Later rounds start when the lead messages you. Send nothing to the lead except what the lead asks for."
5. The rebuttal and final rules, verbatim intent:
   > "When the lead opens a rebuttal round, your peers' positions are in your inbox. Respond to the strongest disagreement: concede or push back with reasons, sending a REBUT to the relevant peers. You may not finalize until you have received and responded to at least two peer messages. When the lead asks for your final, send exactly one message `SendMessage(to=\"team-lead\", summary=\"<name> final position\", message=...)` that starts with the header `[RT:<INV>|FINAL|r<N>] FINAL POSITION`, followed by the lines `PEERS ENGAGED: <names of the peers whose arguments you engaged>`, `CHANGED: <what changed your mind or what you conceded, or why you reaffirmed your position>`, then your full self-contained settled view including where you still disagree and why. It is the only thing the synthesizer will see from you."
6. If `--high-effort`/`--thinking` is set, append: "Extended thinking enabled. Use `[[ ultrathink ]]`. Budget 32,000 thinking tokens."

### 3c. Drive the rounds (stay quiet toward the user)

Do not relay peer chatter, idle notifications or Monitor ticks to the user. Round cap: 3 discussion rounds by default; a teammate sends at most 2 messages to any one peer per round.

1. **Round 1 (opening).** Spawning is round 1. Wait until all five teammates have gone idle (idle notifications).
2. **Round 2 (rebuttal).** `SendMessage` each teammate: "Round 2. Your peers' positions are in your inbox. Respond to the strongest disagreement with a `[RT:<INV>|REBUT|r2]` message to the relevant peers: concede or push back with reasons. Then end your turn." Wait until all are idle.
3. **Round 3 (optional).** Only if positions are still moving or an unresolved disagreement remains: same instruction with `r3`. Skip otherwise.
4. **Final.** `SendMessage` each teammate: "Request for FINAL. Read your inbox once more, then send your `[RT:<INV>|FINAL|r<N>]` FINAL POSITION to team-lead with PEERS ENGAGED and CHANGED lines", with `<N>` set to one past the last discussion round. Arm the stall detector (3d) with that `<N>` as the minimum round.
5. If a FINAL arrives early or without PEERS ENGAGED / CHANGED lines (the detector prints `PREMATURE`), reply to that teammate: "Not yet: read your inbox, respond to a peer's argument, then resend your FINAL." Its earlier FINAL does not count.

### 3d. Arm the stall detector for the final phase

The detector counts only FINALs from this invocation's roster that carry the `[RT:<INV>|FINAL|r<N>]` header with `N` at least the minimum round, name a roster peer other than the sender under `PEERS ENGAGED:`, and state a `CHANGED:` line. Arm a `Monitor` with `command` set to exactly this shell command text, substituting `<SESSION8>` (first 8 characters of the session id), `<INV>`, `<ROSTER_CSV>` (the five full names, comma-separated) and `<N>`:

```text
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; python3 "$PLUGIN_ROOT/scripts/guru_stall.py" "$HOME/.claude/teams/session-<SESSION8>/inboxes/team-lead.json" <INV> <ROSTER_CSV> <N>
```

The inbox location follows the Claude Code agent-teams docs (one team per session named `session-<first 8 chars of session id>`) but has not been confirmed in a live session: check that the file appears once teammates start messaging, and if it does not, locate the lead inbox under `~/.claude/teams/` and pass that path instead. Other `Monitor` fields: `description` `"guru roundtable stall detector"`, `timeout_ms` `1800000`, `persistent` `false`.

The Monitor emits `PROGRESS` as accepted finals land, `PREMATURE` for non-conforming finals, `STALL` (naming idle teammates with no accepted final) after 90 s without progress, and `ALL_REPORTED` then exits. On `STALL`: `SendMessage` each named teammate "Send your FINAL now, following the header format." On `ALL_REPORTED` (or all five accepted finals otherwise in hand): `TaskStop` the Monitor and proceed to Step 4. If a teammate stays unresponsive after two nudges, or the 30-minute cap hits, proceed with the finals in hand and note who did not report.

### 3e. Fallback path — parallel isolated subagents (no cross-talk)

Only if named `Agent` spawns themselves fail, run this self-contained `Bash` call and follow what it prints:

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; cat "$PLUGIN_ROOT/references/guru-chat-fallback.md"
```

## Step 4 — Synthesize

Pass each guru's accepted `FINAL POSITION` report-out (attributed by name, verbatim or faithfully summarized, with the `<INV>-` prefix dropped) to the synthesizer. Tell it these are post-discussion positions and list the concessions and changed minds reported in the `CHANGED:` lines:

```text
Agent(
  subagent_type="tao:perspective-synthesizer",
  model="sonnet",
  prompt="Synthesize this luminary roundtable on: <question>

[For each guru, include their name and their full FINAL POSITION report-out.]

Note which path was used (lead-driven live rounds vs. isolated parallel opinions), how many rounds ran, which positions changed after discussion, and how that affects confidence in the synthesis. Note any guru who did not report in.

Self-contained output (mandatory): the caller sees ONLY your response — never this roundtable. Define each guru's stance IN FULL (20–400 words each; err verbose) before any conclusion references it. Never report 'X argued best / Y was overruled' without first showing the reader what X and Y said."
)
```

The synthesizer's prompt above already mandates self-contained output: its "Perspective Analysis" section defines each guru's stance (20–400 words each) before any conclusion references it, so the caller — who never saw the roundtable directly — understands every position being weighed.

## Step 5 — Present

Lead with which guest luminary was chosen and why, then the synthesizer's output verbatim.
Keep the preamble to factual framing only — guest identity only. Do not mention the path (live vs. fallback) in your preamble; the synthesizer's output already notes the path and confidence implications. Do not draw conclusions or attribute positions in the preamble; all analytical content comes from the synthesizer's output, which defines each guru's stance before referencing it.

After presenting, if the live path ran, tell the user exactly:
> "If you're finished with this guru chat, just say 'done' and I'll send the gurus home."

## Step 6 — Teardown (only after the user says 'done')

Do NOT terminate the teammates when you present the synthesis — leave them idle so the user can open an individual guru's conversation if they wish. This step runs on a **later, separate turn** (after the user explicitly signals they're done), not part of the initial dispatch — resolve the plugin root and load the teardown reference in ONE self-contained `Bash` call, then follow what it prints:

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; cat "$PLUGIN_ROOT/references/guru-chat-teardown.md"
```
