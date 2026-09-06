---
name: requirements
description: "Surface requirements, translate goals to specs"
---

# Tao — Requirements

Requirements discovery and technical translation: surfaces implicit requirements, identifies potential challenges, translates business goals into concrete technical specifications, and makes compelling arguments for proposed solutions.

## Argument handling

- Primary argument: feature, goal, or vague idea — everything in `$ARGUMENTS` after stripping flags
- `--files=<paths>`: existing codebase files for context
- `--focus-areas=<areas>`: specific requirement dimensions to probe (e.g. performance, security, UX)
- `--high-effort` / `--thinking`: add ultrathink instruction to agent prompt

## Dispatch

```text
Agent(
  subagent_type="tao:requirements-architect",
  model="sonnet",
  prompt="Discover and translate requirements for: <feature/goal from $ARGUMENTS>

[If --files: 'Existing codebase context: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for requirements discovery. Budget 32,000 thinking tokens per step.']

Format your response as:
## Business Goals
What this feature/change is actually trying to achieve. Include the implicit goals users didn't state.

## Functional Requirements
User stories in 'As a [role], I want [action] so that [outcome]' format. Group by actor.

## Non-Functional Requirements
Performance targets, security constraints, availability, scalability, compliance, backward compatibility.

## Risks & Open Questions
What could derail this? What decisions need to be made that aren't clear from the brief?

## Proposed Technical Approach
Recommended implementation direction with rationale. Note alternatives considered and why they were ruled out."
)
```
