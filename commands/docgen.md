---
name: docgen
description: "Documentation generation — API docs, architecture docs, usage guides, and inline documentation with consistent formatting. Usage: /tao:docgen [--files=<paths>] [--prompt=<type>]"
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
[If --focus-areas: 'Focus on: <areas>']

Output the generated documentation directly — no preamble, no wrapper, no 'here is the documentation' intro.
The output should be ready to copy and paste into the target location.
Use the format appropriate to the documentation type:
- Inline docstrings: language-native format (Google style for Python, JSDoc for JS/TS, etc.)
- README / guides: GitHub-flavored markdown
- API reference: markdown with consistent method/parameter tables
- Architecture docs: markdown with mermaid or ASCII diagrams where helpful"
)
```
