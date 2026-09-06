# Guru-Chat — Teardown (only after the user says 'done')

Do NOT terminate the teammates when you present the synthesis. Leave them idle so the user can, if they wish, open an individual guru's conversation to see how its thinking evolved over the discussion.

When the user says 'done' (or otherwise signals they are finished with this roundtable):

1. Confirm the current session's active team is still `<TEAM>` (the unique name from Step 3a) before proceeding — if another `/tao` team-mode command ran in the interim, the active context may have shifted.
2. `SendMessage` each teammate `message={type: "shutdown_request"}` (object form — no `summary`).
3. `TaskStop` the Monitor if it is still running.
4. `TeamDelete` once all teammates have shut down.
