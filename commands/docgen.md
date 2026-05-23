---
name: docgen
description: "Documentation generation — API docs, architecture docs, usage guides, and inline documentation with consistent formatting. Usage: /tao:docgen [--files=<paths>] [--prompt=<type>]"
context: fork
---

# Tao — Doc Generator

Automated documentation generation: API docs, architecture docs, usage guides, and inline documentation with consistent formatting.

## Argument handling

- `--files=<paths>`: files/directories to document
- `--prompt=<type>`: documentation type (e.g. "API reference", "README", "architecture overview", "inline docstrings")
- `--focus-areas=<areas>`: specific aspects to document
- Freeform text in `$ARGUMENTS` treated as documentation goal or instructions

## Dispatch

```text
Agent(
  subagent_type="tao:doc-generator",
  model="sonnet",
  prompt="Generate documentation.

[If --files: 'Files to document: <paths>']
[If --prompt or freeform: 'Type/goal: <text>']
[If --focus-areas: 'Focus on: <areas>']"
)
```

Present the agent's response directly to the user as formatted markdown.
