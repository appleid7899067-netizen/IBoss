---
name: skill-installer
description: Install or update reusable OpenCode skills from authoritative URLs or Git repositories by creating project-local .opencode/skills/<name>/SKILL.md files. Use when the user asks to install, add, learn, or save a skill.
---

# Skill Installer

Install skills into the current project under `.opencode/skills/<name>/SKILL.md`.

## Workflow
1. Identify the source URL or repository supplied by the user.
2. If no source is supplied, use websearch to find an authoritative source.
3. Fetch the source with webfetch or inspect the Git repository with git/curl.
4. Extract only actionable instructions, commands, APIs, examples, and important gotchas.
5. If the target skill exists, read it first and merge rather than overwrite blindly.
6. Validate name and description.
7. Write the skill file and verify its path and contents.
8. Report exactly which skill was installed or updated.

Never store secrets, tokens, cookies, or private credentials.
Never copy large source passages verbatim.
