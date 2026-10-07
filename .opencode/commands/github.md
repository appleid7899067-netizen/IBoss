---
description: GitHub operations - read, write, list, commit, branch, and push
agent: operator
---

GitHub operations for $ARGUMENTS.

Use `GITHUB_TOKEN` or `BOSS_GITHUB_TOKEN` from the environment when API authentication is required. Never expose tokens.

Repository: `appleid7899067-netizen/IBoss` unless `BOSS_GITHUB_REPO` overrides it.

Inspect first, make the smallest change, verify with git status/diff and relevant checks, then report the result. Never force-push unless explicitly requested.
