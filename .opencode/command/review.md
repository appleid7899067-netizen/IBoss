---
description: Review current changes or a given file/path for bugs and regressions.
agent: operator
---

Review $ARGUMENTS for correctness, regressions, security issues, and maintainability.

If no target is given, inspect the current git diff and status.

Rules:
- Do not edit files during review.
- Read relevant files and surrounding context.
- List findings by severity with file and line references.
- Include a concrete fix for each finding.
- Finish with a short verification summary.
