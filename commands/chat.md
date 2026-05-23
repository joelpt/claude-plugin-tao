---
name: chat
description: "Collaborative thinking and discussion — brainstorming, problem-solving, and code discussion with optional file context. Usage: /tao:chat <topic or question>"
context: fork
---

# Tao — Chat

Collaborative thinking and discussion partner for brainstorming, problem-solving, and code discussion with optional file context.

## Argument handling

- Primary argument: topic, question, or discussion prompt — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: files to include as context
- `--prompt=<text>`: explicit prompt (alternative to freeform)

## Dispatch

```text
Agent(
  subagent_type="tao:chat-assistant",
  model="sonnet",
  prompt="<topic/question from $ARGUMENTS>

[If --files: 'Context files: <paths>']"
)
```

Present the agent's response directly to the user as formatted markdown.
