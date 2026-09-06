# Guru-Chat — Fallback path (TeamCreate unavailable)

If `TeamCreate` is blocked, errors, or is unavailable for ANY reason:
Report that explicitly to the user — e.g. "Team mode unavailable (`<reason>`); falling back to parallel independent subagents — the gurus give isolated opinions with no live discussion." Then dispatch all five luminaries in ONE message as parallel `Agent` calls (`subagent_type="general-purpose"`, `model="sonnet"`).
Each prompt: the persona brief, the user's question, any `--files` context, and "Give your candid, in-character take. Be specific and technical." If `--high-effort`/`--thinking` is set, append the same `[[ ultrathink ]]` / 32,000-token instruction.
Collect the five independent responses. There is no discussion or report-out protocol in this mode (no team, no Monitor, no deferred teardown — skip Step 6).
