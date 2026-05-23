---
name: clink
description: "External CLI integration bridging — guidance on integrating tao workflows with external CLI tools and optimizing requests for different AI CLIs. Usage: /tao:clink --cli-name=<name> [--prompt=<task>]"
context: fork
---

# Tao — Clink

External CLI integration bridging: provides guidance on integrating tao reasoning workflows with external CLI tools and optimizing requests for different AI CLI tools.

## Argument handling

- `--cli-name=<name>`: target CLI tool (e.g. aider, continue, cursor)
- `--prompt=<text>`: specific integration task or question
- Freeform text in `$ARGUMENTS` treated as the integration goal

## Dispatch

```text
Agent(
  subagent_type="tao:clink-assistant",
  model="sonnet",
  prompt="Provide CLI integration guidance.

[If --cli-name: 'Target CLI: <name>']
[If --prompt or freeform: '<task/goal>']"
)
```

Present the agent's response directly to the user as formatted markdown.
