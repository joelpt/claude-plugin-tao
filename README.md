# tao

Advanced multi-model AI reasoning workflows for Claude Code: complex decision analysis,
debugging, code review, and technical architecture. Routes each task type to the optimal
Claude model tier (Opus / Sonnet / Haiku).

## Install

```bash
claude plugin marketplace add joelpt/joelpt-claude-plugins
claude plugin install tao@joelpt-claude-plugins
```

Then restart Claude Code. Requires read access to the private marketplace repo (`gh auth login`).

## Layout

```text
.claude-plugin/plugin.json   ← plugin manifest
commands/                    ← reasoning-workflow slash commands
agents/                      ← specialized reasoning subagents
```

Distributed via the [`joelpt-claude-plugins`](https://github.com/joelpt/joelpt-claude-plugins)
marketplace. Bump `.claude-plugin/plugin.json` `version` (patch minimum) on any change — the
marketplace cache is keyed by version.

## License

MIT. See `LICENSE`.
