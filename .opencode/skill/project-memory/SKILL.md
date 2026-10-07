---
name: project-memory
description: Maintain concise project memory from verified repository facts, decisions, conventions, and completed work so future agent tasks can continue consistently.
---

# Project Memory

Keep project memory in the existing repository structure. Do not create a separate database or external memory service.

## Rules

1. Before a complex task, inspect the repository for existing project context and relevant configuration.
2. Treat repository files, current code, and explicit user decisions as authoritative.
3. Record only durable project facts:
   - architecture and important entry points
   - commands used to build, test, or deploy
   - important conventions
   - decisions that affect future implementation
   - verified fixes and known limitations
4. Do not store secrets, API keys, tokens, cookies, personal credentials, or transient chat content.
5. Prefer updating an existing project documentation/context file when one already serves this purpose.
6. If no suitable memory file exists, keep the memory in the current task context rather than creating a new system automatically.
7. Before changing code based on remembered information, verify the relevant files still match that memory.
8. Remove or correct stale memory when repository evidence contradicts it.

## Workflow

1. Inspect existing project documentation and configuration.
2. Extract only durable, verified facts.
3. Reuse those facts when planning or implementing later work.
4. Verify assumptions against the current repository before editing.
5. After a significant completed change, update the existing project context documentation if appropriate.

Never expose or persist secrets.
