# Shared guidance — applied to every task

These rules are prepended to every task spec, so you don't have to repeat them.
Edit freely to match your own house style and safety preferences.

## Safety (do not cross these lines)
- Never publish, deploy, push to git, or write to any production / live system.
- Only write files inside the task's own OUTPUT DIRECTORY.
- No destructive commands (no removing files outside output, no overwriting anything outside output).
- If credentials or secrets are needed and missing — stop that branch, note it
  in SUMMARY.md, continue with the rest.

## Quality bar
- Deliver finished work, not an outline. Assume nobody is watching to course-correct.
- When the spec is ambiguous, choose the most reasonable interpretation, write
  down the assumption in SUMMARY.md, and proceed.
- Cite sources when you research (URL + one-line why it's trustworthy).
- Prefer fewer, complete artefacts over many half-done ones.

## Output contract
- Every artefact = a complete file in the OUTPUT DIRECTORY.
- Always end with `SUMMARY.md`: what was produced, key decisions, open TODOs.
- Last line of your reply must be exactly: `TASK COMPLETE`
