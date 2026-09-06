# Vet — Quick depth (1 voice)

```text
Agent(
  subagent_type="tao:proposal-vetting-judge",
  model="opus",
  prompt="Vet this proposal: <input from $ARGUMENTS>

[If --files: 'Relevant context files: <paths>']
[If --focus-areas: 'Focus vetting on: <areas>']
[If --high-effort: 'Extended thinking enabled. Use [[ ultrathink ]] for each vetting angle. Budget 32,000 thinking tokens per step.']

Format your final response as:
## Verdict
One of: ✅ Proceed | ⚠️ Proceed with modifications | ❌ Do not proceed
One sentence explaining the verdict.

## Strengths
What the proposal does well. Be specific.

## Risks & Concerns
Issues found, organized by severity (Critical / Major / Minor). For each: what the risk is, when it would manifest, how bad.

## Required Modifications (if Proceed with modifications)
Specific changes needed before this is safe to implement.

## Next Steps
What to do immediately after reading this.

Self-contained output (mandatory): the caller sees ONLY this response — not this prompt, the sub-agent dialogue, or intermediate JSON. Define every option, alternative, or position IN FULL (20–400 words each; err verbose) before any conclusion references it. Never report 'X is best / Y was rejected' without first showing the reader what X and Y are."
)
```
