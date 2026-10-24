---
name: guru-chat
description: "Live roundtable of domain-suited luminaries"
---

# Tao Guru-Chat Mode

Convene a roundtable of luminaries suited to the question who hold a live, round-by-round discussion among themselves, then run their settled positions through `tao:perspective-synthesizer` for a unified takeaway.

The point is epistemic diversity from strongly-opinionated, distinct philosophies — not consensus theater.
Keep each persona technically substantive and in-character; avoid caricature, hero-worship, or putting words in their mouths that contradict their well-known positions.

## The Panel

You, the lead, choose the panel for every question. It is five luminaries by default (three to seven when the question warrants), each a real person, living or historical, with a substantial public body of work to ground their lens.

**Suggested default for software questions.** When the question is about building, running or reviewing software, start from these four and add a domain-matched fifth (Step 2). Swap any of them, or add a second domain seat, whenever someone else would serve the question better:

- **Linus Torvalds** — creator of Linux and Git. Lens: kernel-grade pragmatism, "good taste" in data structures, ruthless simplicity, distrust of abstraction-for-its-own-sake and over-engineering, blunt about bad design and premature complexity.
- **Guido van Rossum** — creator of Python. Lens: readability counts, "one obvious way to do it", developer ergonomics and humane APIs, gradual/optional typing, evolving a language without breaking its users.
- **Anders Hejlsberg** — lead architect of C#, TypeScript, Turbo Pascal, Delphi. Lens: pragmatic type systems, structural/gradual typing layered onto existing ecosystems, world-class tooling and IDE experience, language design at industrial scale.
- **John Carmack** — id Software, Oculus. Lens: first-principles engineering, performance and latency, low-level reasoning, rapid iteration, measuring instead of guessing, cutting scope to ship.

This is a suggestion, not a roster. A retirement-income question gets an economist, a practitioner and a skeptic, not four programmers.

## Step 1 — Parse arguments

The question/topic is everything in `$ARGUMENTS` after stripping flags.

Recognized flags:

- `--files=<paths>` → file/directory paths the gurus should read for grounding before opining
- `--panel=<names>` → comma-separated people to use as the panel instead of choosing one (Step 2)
- `--high-effort` / `--thinking` → spawn persona subagents with `[[ ultrathink ]]` and a larger reasoning budget

If a project is present (README, CLAUDE.md, source tree), the gurus may read it for context so their advice fits the actual codebase rather than generic principles.

## Step 2 — Choose the panel

Classify the question first, then pick the panel:

- **Software / engineering** → start from the suggested default and add the domain-matched fifth seat (guidance below). Replace or add anyone who would serve the question better.
- **Anything else** → do not use the software default. Choose figures suited to the subject, e.g. for policy an economist, a legal scholar, a practitioner and a skeptic or ethicist; for personal finance a financial economist, a planner and a behavioral scientist.
- **Mixed** → keep at least one engineer alongside the domain figures.

Rules for every topic:

- Lens diversity: complementary expertise, and at least one dissenting, adversarial or outsider view.
- Every member must be well documented: someone whose position you can characterize from their own books, papers or talks. Do not pick someone you could only caricature.
- No duplicates. Five by default, three to seven allowed. If the question spans fields, give each field a seat (two guests is fine).
- `--panel=<names>` (comma-separated) means use exactly those people and skip the classification. You still write a lens brief for each.

State the panel and a one-line rationale for each member BEFORE dispatching. For anyone outside the suggested four, write a 1-2 sentence lens brief grounded in their cited public work.

Persona rule: every panelist is an explicitly simulated analytical lens built from public work. Say so in each spawn prompt, and tell it never to present generated statements as authentic quotations or endorsements by the real person.

Guidance for the domain seat on software questions (illustrative, not exhaustive):

- Distributed systems / consensus → Leslie Lamport
- Databases / storage engines → Michael Stonebraker
- Functional programming / language semantics → Rich Hickey or Simon Peyton Jones
- Machine learning / AI systems → Andrej Karpathy or Geoffrey Hinton
- Frontend / UI frameworks → Evan You or Dan Abramov
- Systems / observability / Rust → Bryan Cantrill
- Security / cryptography → Daniel J. Bernstein or Bruce Schneier
- Cloud / large-scale infrastructure → Jeff Dean

If nothing is clearly more relevant, default to a generalist systems thinker (e.g. Rich Hickey) and say so.

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

Teammate names are `<INV>-<slug>`, one per panelist (the roster). `<slug>` is a short lowercase handle matching `[a-z0-9-]+`, unique within the panel and normally the surname (e.g. `sharpe`, `lamport`, `peyton-jones`; the suggested software four use `linus`, `guido`, `anders`, `carmack`). Use that same slug in the `Agent` name, in `<ROSTER_CSV>`, and when teammates write `PEERS ENGAGED:`. The prefix keeps a second roundtable in the same session, or any unrelated teammate, from being mixed up with this one.

The lead's address is `team-lead` (the verified address). Do not use `main`: it has been rejected for teammates.

### 3b. Spawn every panelist in ONE message (parallel)

Each via the `Agent` tool with `name="<INV>-<luminary>"`, `subagent_type="general-purpose"`, and **`model="sonnet"`** (all panelists on the same tier — the value here is perspective diversity from the personas, not model diversity). If a named spawn itself errors, go to 3e and state the real error; never fall back because of a keyword search for a missing tool.

Each spawn prompt MUST contain:

1. The persona brief for that luminary (from The Panel or your Step 2 lens brief), the simulated-lens rule from Step 2, and the instruction to stay substantive and in-character.
2. The user's question/topic and any `--files` context.
3. The full roster of peer names (exact `<INV>-...` names) and the invocation id.
4. The round protocol, verbatim intent:
   > "This roundtable is run in rounds by the lead. Every message you send MUST begin with the header `[RT:<INV>|<TYPE>|r<N>]` (TYPE is OPEN, REBUT or FINAL; N is the round number the lead gave you). Spawning you is round 1 (use `r1`, TYPE OPEN). Send your opening position to ALL peers with `SendMessage(to=\"<peer>\")`, then END YOUR TURN and do nothing else. Messages from peers are only delivered after your turn ends, so do not wait inside a turn and do not finalize now. Later rounds start when the lead messages you. In any one round send at most 2 messages to any single peer. Send nothing to the lead except what the lead asks for."
5. The rebuttal and final rules, verbatim intent:
   > "When the lead opens a rebuttal round, your peers' positions are in your inbox. Respond to the strongest disagreement: concede or push back with reasons, sending a REBUT to the relevant peers. You may not finalize until you have received and responded to at least two peer messages. When the lead asks for your final, send exactly one message `SendMessage(to=\"team-lead\", summary=\"<name> final position\", message=...)` that starts with the header `[RT:<INV>|FINAL|r<N>] FINAL POSITION`, followed by the lines `PEERS ENGAGED: <names of the peers whose arguments you engaged>`, `CHANGED: <what changed your mind or what you conceded, or why you reaffirmed your position>`, then your full self-contained settled view including where you still disagree and why. It is the only thing the synthesizer will see from you."
6. If `--high-effort`/`--thinking` is set, append: "Extended thinking enabled. Use `[[ ultrathink ]]`. Budget 32,000 thinking tokens."

### 3c. Drive the rounds (stay quiet toward the user)

Do not relay peer chatter, idle notifications or Monitor ticks to the user. Round cap: 3 discussion rounds by default; a teammate sends at most 2 messages to any one peer per round.

1. **Round 1 (opening).** Spawning is round 1. Wait until all teammates have gone idle. Peer messages can wake an already-idle teammate, so do not count any idle: count only the idle notification that follows each teammate's turn after your round request (a teammate that wakes again to read peer mail produces another idle; wait for it to settle).
2. **Round 2 (rebuttal).** `SendMessage` each teammate: "Round 2. Your peers' positions are in your inbox. Respond to the strongest disagreement with a `[RT:<INV>|REBUT|r2]` message to the relevant peers: concede or push back with reasons. Then end your turn." Wait for the idle notification that follows each teammate's turn on this request, as in round 1.
3. **Round 3 (optional).** Only if positions are still moving or an unresolved disagreement remains: same instruction with `r3`. Skip otherwise.
4. **Final.** `SendMessage` each teammate: "Request for FINAL. Read your inbox once more, then send your `[RT:<INV>|FINAL|r<N>]` FINAL POSITION to team-lead with PEERS ENGAGED and CHANGED lines", with `<N>` set to one past the last discussion round. Arm the stall detector (3d) with that `<N>` as the minimum round.
5. If a FINAL arrives early or without PEERS ENGAGED / CHANGED lines (the detector prints `PREMATURE`), reply to that teammate: "Not yet: read your inbox, respond to a peer's argument, then resend your FINAL." Its earlier FINAL does not count.

### 3d. Arm the stall detector for the final phase

The detector counts only FINALs from this invocation's roster that carry the `[RT:<INV>|FINAL|r<N>]` header with `N` at least the minimum round, name a roster peer other than the sender under `PEERS ENGAGED:`, and state a `CHANGED:` line. Arm a `Monitor` with `command` set to exactly this shell command text, substituting `<SESSION8>` (first 8 characters of the current session id, i.e. the id shown in the transcript path or session context; the docs name the implicit team `session-<SESSION8>`), `<INV>`, `<ROSTER_CSV>` (every panelist's full name, comma-separated) and `<N>`:

```text
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; python3 "$PLUGIN_ROOT/scripts/guru_stall.py" "$HOME/.claude/teams/session-<SESSION8>/inboxes/team-lead.json" <INV> <ROSTER_CSV> <N>
```

The inbox location follows the Claude Code agent-teams docs (one team per session named `session-<first 8 chars of session id>`) but has not been confirmed in a live session: check that the file appears once teammates start messaging. The detector prints `INBOX_MISSING <path>` when it does not exist: then locate the lead inbox under `~/.claude/teams/` and pass that path instead. Other `Monitor` fields: `description` `"guru roundtable stall detector"`, `timeout_ms` `1800000`, `persistent` `false`.

The Monitor emits `INBOX_MISSING` / `INBOX_INVALID` when the inbox file is absent or not a JSON list, `PROGRESS` as accepted finals land, `PREMATURE` for non-conforming finals, `STALL` (naming stuck teammates, `stuck=[...]`: those whose latest message is an idle notification or a non-conforming FINAL, with no accepted final) after 90 s without progress, and `ALL_REPORTED` then exits. On `STALL`: `SendMessage` each named teammate "Send your FINAL now, following the header format." On `ALL_REPORTED` (or every panelist's accepted final otherwise in hand): `TaskStop` the Monitor and proceed to Step 4. If a teammate stays unresponsive after two nudges, or the 30-minute cap hits, proceed with the finals in hand and note who did not report.

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

Lead with the panel and a one-line rationale for each member, then the synthesizer's output verbatim.
Keep the preamble to factual framing only — panel composition only. Do not mention the path (live vs. fallback) in your preamble; the synthesizer's output already notes the path and confidence implications. Do not draw conclusions or attribute positions in the preamble; all analytical content comes from the synthesizer's output, which defines each guru's stance before referencing it.

### Roundtable stats (live path only)

After the synthesizer's output, append a `## Roundtable stats` section: one row per teammate with tokens, messages sent, messages received, wall-clock time and a 1-5 star contribution score. Skip it on the fallback path, which has no teammates. Run this in ONE self-contained `Bash` call, substituting `<INV>` and `<ROSTER_CSV>` (every panelist's full name, comma-separated) as in 3d:

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; python3 "$PLUGIN_ROOT/scripts/guru_stats.py" "$CLAUDE_CODE_SESSION_ID" <INV> <ROSTER_CSV>
```

It reads each teammate's transcript and prints the table with every score `unrated`, followed by a `Cited by peers' FINALs:` line. Rate each teammate yourself, then rerun the same command with `--stars <name>=<1-5>,...` (short names, e.g. `--stars linus=4,guido=5`) and present that table. Rate contribution to the outcome, not agreement with you, length or token spend:

- 5: their argument moved other teammates (peers' `CHANGED:` lines credit it, and several peers cite them).
- 4: sharp, substantive engagement; forced a concession or conceded for a good reason.
- 3: solid and sound, but largely what was expected of the role.
- 2: restated the opening position with little engagement.
- 1: negligible, or did not report in.

If `CLAUDE_CODE_SESSION_ID` is empty, pass the session id from the transcript path instead. Add one line under the table: tokens are input plus cache plus output (the figure in brackets is output only), and wall clock runs from spawn to the last activity, including time idle between rounds. A teammate with no transcript shows `no transcript found`.

After presenting, if the live path ran, tell the user exactly:
> "If you're finished with this guru chat, just say 'done' and I'll send the gurus home."

## Step 6 — Teardown (only after the user says 'done')

Do NOT terminate the teammates when you present the synthesis — leave them idle so the user can open an individual guru's conversation if they wish. This step runs on a **later, separate turn** (after the user explicitly signals they're done), not part of the initial dispatch — resolve the plugin root and load the teardown reference in ONE self-contained `Bash` call, then follow what it prints:

```bash
PLUGIN_ROOT="${TAO_PLUGIN_ROOT:-$(dirname "${TAO_SCRIPTS:-$HOME/code/claude-plugin-tao/scripts}")}"; cat "$PLUGIN_ROOT/references/guru-chat-teardown.md"
```
