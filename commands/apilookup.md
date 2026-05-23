---
name: apilookup
description: "API and library research — finds official docs, current version, quick-start patterns, and common pitfalls using web search. Usage: /tao:apilookup <library or API name>"
context: fork
---

# Tao — API Lookup

Inline API and library research mode (no sub-agent). Finds official documentation, current version, quick-start patterns, authentication requirements, and common pitfalls via web search.

## Dispatch

No agent needed — run inline with web search tools.

Output this research guidance, then use WebSearch/WebFetch to research the query:

```text
RESEARCH: <query from $ARGUMENTS>

1. Identify official documentation site
2. Verify current version and check for breaking changes
3. Search for: "<query> official documentation", "<query> latest examples <current-year>"
4. Locate: installation, quick start, API reference, common patterns
5. Capture: core concepts, key functions, auth requirements, common pitfalls
```

Present findings to the user as formatted markdown with code examples where useful.
