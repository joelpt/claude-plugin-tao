---
name: chat
description: "Collaborative thinking and discussion — brainstorming, problem-solving, and code discussion with optional file context. Usage: /tao:chat <topic or question>"
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

[If --files: 'Context files: <paths>']

Respond conversationally. Match the register and depth of the question — a quick question gets a direct answer, a nuanced question gets nuanced treatment. Use structure (headers, bullets, code blocks) only when it genuinely aids clarity, not by default. Think out loud where it helps the user follow your reasoning."
)
```
