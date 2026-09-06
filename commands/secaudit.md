---
name: secaudit
description: "OWASP security and compliance assessment"
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
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for threat modeling steps. Budget 32,000 thinking tokens per step.']

Format your response as:
## Executive Summary
Total findings by severity (Critical: N, High: N, Medium: N, Low: N). One-paragraph risk posture.

## Findings
Group by OWASP category or threat domain. For each finding:
**[SEVERITY] Title** — file:line if applicable
Description of the vulnerability, attack scenario, and remediation.

## Remediation Plan
Prioritized list: fix in this sprint / fix this quarter / track as debt.

## Compliance Notes (if applicable)
Any observations relevant to SOC2, GDPR, PCI-DSS, HIPAA."
)
```
