---
name: testgen
description: "Test suite generation with comprehensive edge case analysis — plans testing strategy, identifies edge cases, and produces implementable test specifications. Usage: /tao:testgen [--files=<paths>] [<focus>]"
context: fork
---

# Tao — Test Generator

Test suite generation with comprehensive edge case analysis: plans testing strategy, identifies edge cases, and provides implementable test specifications.

## Argument handling

- `--files=<paths>`: files/modules to generate tests for
- `--focus-areas=<areas>`: specific test categories (e.g. unit, integration, edge cases, error paths)
- Freeform text in `$ARGUMENTS` treated as the testing goal or constraints

## Dispatch

```text
Agent(
  subagent_type="tao:test-generator",
  model="sonnet",
  prompt="Generate a comprehensive test suite.

[If --files: 'Code to test: <paths>']
[If --focus-areas: 'Focus on: <areas>']
[If freeform: '<goal/constraints>']

Format your response as:
## Test Strategy
What approach and test categories you're covering and why (unit / integration / e2e, coverage targets, key invariants).

## Test Cases
Organized by category (Happy Path, Edge Cases, Error Paths, Concurrency/Performance if applicable).
For each test case: name, setup, action, expected outcome.
Write actual test code in the project's test framework where you can infer it from the files. Use pseudocode only when the framework is unknown."
)
```
