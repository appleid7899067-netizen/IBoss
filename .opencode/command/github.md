---
description: GitHub operations - read, write, list, commit, branch, and push
agent: operator
---

GitHub operations for $ARGUMENTS.

Repository: `appleid7899067-netizen/IBoss` by default. Use `BOSS_GITHUB_REPO` to override.

Authentication:
- Use `GITHUB_TOKEN` or `BOSS_GITHUB_TOKEN` from the environment.
- Never print, expose, commit, or write the token into files.
- If no token is available, report that clearly.

Operations:
- `read <path>` — read a repository file
- `write <path> <content>` — create or update a repository file
- `list` — list repository files
- `branch <name>` — create or switch to a branch when supported
- `commit <message>` — create a local commit
- `push` — push commits to the configured remote

Workflow:
1. Inspect the current repository state before changing anything.
2. Make the smallest correct change.
3. Verify the result with git diff/status and relevant tests.
4. Never force-push unless the user explicitly asks.
