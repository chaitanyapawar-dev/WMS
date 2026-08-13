# Eigi Skills

Reusable Codex skills for Eigi engineering workflows.

This repo stores shared standards under `.codex/skills/` so they can be copied into any Eigi repo and used by Codex when creating, modifying, reviewing, or testing app code.

## Available Skills

- `.codex/skills/wms-backend-standards`: Backend API standards for Python/FastAPI-style services, folder structure, routes, controllers, CRUD, services, logging, docstrings, tests, and backend `.gitignore` hygiene.
- `.codex/skills/wms-frontend-standards`: Frontend web app standards for routes/pages, feature components, shared UI, API clients, hooks/stores, styling, tests, environment handling, and frontend `.gitignore` hygiene.

## How To Use

Copy the `.codex/skills/` folder into the target WMS repo. Then add a short durable note to the repo's agent guide so Codex knows when to use the skills.

Use this short snippet in the target repo's `AGENT.md` or `AGENTS.md`:

```markdown
## WMS Skills

Use `.codex/skills/wms-backend-standards` for WMS backend API work.
It guides route, controller, CRUD, service, schema, model, logging, docstring, test, and backend `.gitignore` standards.
Use `.codex/skills/wms-frontend-standards` for WMS frontend web app work.
It guides route/page, feature component, shared UI, API client, hook/store, styling, test, env, and frontend `.gitignore` standards.
Inspect nearby code first and follow the closest local convention.
Read the matching `SKILL.md` first and load references only when needed.
```

## Skill Layout

```text
.codex/skills/
  wms-backend-standards/
    SKILL.md
    references/
      folder-structure.md
      examples.md
  wms-frontend-standards/
    SKILL.md
    references/
      folder-structure.md
```

## Validation

After editing a skill, run:

```bash
python3 /Users/mrunmaychichkhede/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/wms-backend-standards
python3 /Users/mrunmaychichkhede/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/wms-frontend-standards
```

Keep skill instructions concise. Put detailed repeatable guidance in `SKILL.md` and only add reference files when the extra context should be loaded on demand.
