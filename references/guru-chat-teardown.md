# Guru-Chat — Teardown (only after the user says 'done')

Do NOT terminate the teammates when you present the synthesis. Leave them idle so the user can, if they wish, open an individual guru's conversation to see how its thinking evolved over the discussion.

When the user says 'done' (or otherwise signals they are finished with this roundtable):

1. Scope teardown to this roundtable's roster only: the `<INV>-...` names from Step 3a. Never touch other teammates in the session, including those of another roundtable.
2. `SendMessage` each roster teammate `message={type: "shutdown_request"}` (object form — no `summary`). A teammate that has already exited is fine; skip it.
3. `TaskStop` the Monitor if it is still running.
4. There is no team to delete: the session's single implicit team is not ours to remove. Teardown is complete once the roster teammates have shut down.
