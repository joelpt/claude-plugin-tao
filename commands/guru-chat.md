---
name: guru-chat
description: "Roundtable of software-engineering luminaries: Linus Torvalds, Guido van Rossum, Anders Hejlsberg, John Carmack + one question-relevant guest, discussing your question, then synthesized. Usage: /tao:guru-chat <question or topic>"
context: fork
---

# Tao Guru-Chat Mode

Convene a roundtable of legendary software engineers to discuss the user's question, then run the discussion through `tao:perspective-synthesizer` for a unified takeaway.

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

## Step 3 — Hold the roundtable

**Preferred path — a real team that talks to itself.**
Attempt to convene the panel as a team so the gurus can react to each other:

1. `TeamCreate(team_name="guru-roundtable", description="<short topic>")`.
2. Spawn all five luminaries as teammates in ONE message (parallel), each via the `Agent` tool with `team_name="guru-roundtable"`, a `name` (e.g. `linus`, `guido`, `anders`, `carmack`, `<guest>`), `subagent_type="general-purpose"`, and `model="opus"`. Each prompt: the persona brief above, the user's question, any `--files` context, and "Give your opening position in character — specific and technical." If `--high-effort`/`--thinking` is set, append: "Extended thinking enabled. Use `[[ ultrathink ]]`. Budget 32,000 thinking tokens." Each `Agent` call returns that teammate's opening position as its result — collect the five returns directly; you do not need to poll a mailbox.
3. Relay the five openings to each guru with `SendMessage` (string messages require a `summary`, e.g. `SendMessage(to="guido", summary="peer openings for rebuttal", message="<the other four openings> — where do you agree, push back, or spot something a peer missed? One round.")`). Each teammate's reply is delivered back to you automatically as a new turn; collect those five rebuttals.
4. The transcript (five openings + five rebuttals) is the roundtable.
5. Shut the team down cleanly: `SendMessage` each teammate `message={type: "shutdown_request"}` (object form — no `summary` needed), then `TeamDelete`.

**If `TeamCreate` is blocked, errors, or is unavailable for ANY reason:**
Report that explicitly to the user — e.g. "Team mode unavailable (`<reason>`); falling back to parallel independent subagents — the gurus give isolated opinions with no cross-talk." Then run the fallback.

**Fallback path — parallel isolated subagents (no cross-talk).**
Dispatch all five luminaries in ONE message as parallel `Agent` calls (`subagent_type="general-purpose"`, `model="opus"`).
Each prompt: the persona brief, the user's question, any `--files` context, and "Give your candid, in-character take. Be specific and technical." If `--high-effort`/`--thinking` is set, append the same `[[ ultrathink ]]` / 32,000-token instruction as the team path.
Collect the five independent responses. There is no rebuttal round in this mode.

Bound the cost: one opening round plus at most one rebuttal round (team path), or a single round (fallback). Do not loop indefinitely.

## Step 4 — Synthesize

Pass the full roundtable (every guru's contribution, attributed by name) to the synthesizer:

```text
Agent(
  subagent_type="tao:perspective-synthesizer",
  model="sonnet",
  prompt="Synthesize this luminary roundtable on: <question>

[For each guru, include their name and their full contribution — opening position and any rebuttal — verbatim or faithfully summarized.]

Note which path was used (team discussion vs. isolated parallel opinions) and how that affects confidence in the synthesis.

Self-contained output (mandatory): the caller sees ONLY your response — never this roundtable. Define each guru's stance IN FULL (20–400 words each; err verbose) before any conclusion references it. Never report 'X argued best / Y was overruled' without first showing the reader what X and Y said."
)
```

The synthesizer's output already enforces the Self-Contained Output Contract: its "Perspective Analysis" section defines each guru's stance (20–400 words each) before any conclusion references it, so the caller — who never saw the roundtable directly — understands every position being weighed.

## Step 5 — Present

Lead with which guest luminary was chosen and why, then which path ran (team discussion or isolated fallback, with the reason if it fell back), then the synthesizer's output verbatim.
Keep the preamble to factual framing only — guest identity and path reason. Do not draw conclusions or attribute positions in the preamble; all analytical content comes from the synthesizer's output, which defines each guru's stance before referencing it.
