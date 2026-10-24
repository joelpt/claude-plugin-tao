# Guru-Chat — Fallback path (named spawns failed)

Use this only when a named `Agent` spawn itself failed. Tell the user the real reason — e.g. "Live roundtable unavailable (`<actual error from the named Agent spawn>`); falling back to parallel independent subagents — the gurus give isolated opinions with no live discussion." Then dispatch every panelist in ONE message as parallel `Agent` calls (`subagent_type="general-purpose"`, `model="sonnet"`, no `name`).
Each prompt: the persona brief, the user's question, any `--files` context, and "Give your candid, in-character take. Be specific and technical." If `--high-effort`/`--thinking` is set, append the same `[[ ultrathink ]]` / 32,000-token instruction.
Collect the independent responses. There is no discussion or report-out protocol in this mode (no rounds, no Monitor, no deferred teardown — skip Step 6).
