---
name: multi-agent
description: Coordinate specialized OpenCode agents for complex work by delegating research, implementation, review, and verification to focused subagents. Use when a task benefits from staged or parallel agent work.
---

# Multi-Agent

This deployment is memory-constrained. Do not spawn subagents here; the project denies the `task` tool to avoid additional server memory use.

Only use the `task` tool when project permissions allow it and the runtime has enough memory for additional agents. In this deployment, keep all work in the primary agent.

## Roles
- Researcher: inspect documentation, APIs, and project context.
- Coder: implement the smallest correct change.
- Reviewer: inspect changes without editing.
- Tester: run focused tests and diagnose failures.

## Workflow
1. If subagents are unavailable or denied, complete the work in the primary agent. Otherwise, split complex work into independent or sequential pieces.
2. Delegate research or exploration when useful.
3. Give implementation agents precise acceptance criteria.
4. Ask a reviewer to inspect resulting changes.
5. Run verification after implementation.
6. The primary agent owns the final decision and summary.

Avoid unnecessary delegation for small tasks.
Do not ask multiple agents to edit the same file concurrently.
