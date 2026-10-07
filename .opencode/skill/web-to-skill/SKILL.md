---
name: web-to-skill
description: Use when the user wants to fetch information from websites, docs, or URLs and save it as a permanent reusable skill (SKILL.md) in ~/.config/opencode/skills. Triggers - "turn this site into a skill", "save docs as skill", "learn from this URL", "ดึงข้อมูลจากเว็บมาเป็นทักษะ".
---

# Web to Skill

Turn web content into a permanent opencode skill.

## Workflow

1. Collect the URLs from the user. If none are given, use `websearch` to find authoritative sources (official docs first).
2. Fetch each page with `webfetch` (format `markdown`). Follow links to relevant subpages only when needed.
3. Distill the content. Keep only what an agent needs to act: key concepts, exact commands, API shapes, minimal examples, gotchas. Drop navigation, marketing, and duplicated text.
4. Choose a skill name: lowercase, hyphen-separated, max 64 chars.
5. Write `~/.config/opencode/skills/<name>/SKILL.md` with this frontmatter:

```markdown
---
name: <name>
description: <What it covers AND when to use it, third person, with concrete trigger keywords>
---
```

6. Body structure: overview, quick reference, step-by-step usage, examples, and a `## Sources` section listing every URL with the fetch date.
7. For large material, put details in sibling files (e.g. `reference/api.md`) and link them from `SKILL.md`.
8. Tell the user the skill path and that opencode must be restarted to load it.

## Rules

- Never copy long passages verbatim; summarize and cite the source URL.
- Never store secrets, tokens, or cookies found on pages.
- If the skill already exists, read it first and merge instead of overwriting.
- Folder name must equal the `name` field.
