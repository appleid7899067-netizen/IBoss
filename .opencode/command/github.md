---
description: GitHub operations - read/write files, create repos, push commits
agent: build
---

GitHub operations for $ARGUMENTS

Use the GitHub API with the token from environment variable `GITHUB_TOKEN` or `BOSS_GITHUB_TOKEN`.

Operations:
- `read <path>` - Read a file from the repo
- `write <path> <content>` - Write/update a file
- `list` - List files in repo root
- `create-repo <name>` - Create a new repository
- `push` - Push local commits to remote

Repo: `appleid7899067-netizen/IBoss` (or set `BOSS_GITHUB_REPO`)

If no token is available, tell the user to set `GITHUB_TOKEN` or `BOSS_GITHUB_TOKEN`.
