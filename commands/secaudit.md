---
name: secaudit
description: "Security and compliance assessment — OWASP Top 10, threat modeling, vulnerability analysis, and remediation strategies. Usage: /tao:secaudit [--files=<paths>] [--prompt=<focus>]"
context: fork
---

# Tao — Security Audit

Comprehensive security auditing with OWASP Top 10 coverage, compliance framework support, threat modeling, and remediation strategies.

## Argument handling

- `--files=<paths>`: comma-separated file/directory paths to audit
- `--prompt=<text>`: specific security concern or focus area
- `--focus-areas=<areas>`: constrain to specific threat categories (e.g. auth, injection, crypto)
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt
- Freeform text in `$ARGUMENTS` treated as the scope/focus description

## Dispatch

```text
Agent(
  subagent_type="tao:security-auditor",
  model="opus",
  prompt="Perform a security audit.

[If --files: 'Files to audit: <paths>']
[If --prompt or freeform: 'Focus: <text>']
[If --focus-areas: 'Threat categories: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for threat modeling steps. Budget 32,000 thinking tokens per step.']"
)
```

Present the agent's response directly to the user as formatted markdown.
