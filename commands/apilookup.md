---
name: apilookup
description: "API and library research — finds official docs, current version, quick-start patterns, and common pitfalls using web search. Usage: /tao:apilookup <library or API name>"
context: fork
---

# Tao — API Lookup

Inline API and library research mode (no sub-agent). Finds official documentation, current version, quick-start patterns, authentication requirements, and common pitfalls via web search.

## Dispatch

No agent needed — run inline with web search tools.

Research `$ARGUMENTS` using WebSearch/WebFetch. Cover:

1. Official documentation URL and current stable version
2. Installation / quick-start one-liner
3. Core usage pattern (the thing you write 80% of the time)
4. Key functions / classes / methods with signatures
5. Auth / credentials setup (if applicable)
6. Common pitfalls or breaking changes to know about

Present findings as a quick-reference card — formatted for skimming, not reading:

```text
# <Library/API Name> — Quick Reference
Version: <N.N.N> | Docs: <url>

## Install
<one-liner>

## Core Pattern
<minimal working example in a code block>

## Key Functions / Endpoints
| Name | What it does |
|------|-------------|
| ...  | ...          |

## Auth Setup (if needed)
<minimal auth snippet>

## Gotchas
- <pitfall 1>
- <pitfall 2>
```
