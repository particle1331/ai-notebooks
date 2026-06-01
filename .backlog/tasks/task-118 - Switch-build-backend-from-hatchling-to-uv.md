---
id: TASK-118
title: Switch build backend from hatchling to uv
status: To Do
assignee: []
created_date: '2026-06-09 10:39'
updated_date: '2026-06-09 11:16'
labels: []
milestone: m-00
dependencies: []
priority: low
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
All `pyproject.toml` files in the repo (root + workspace members) currently use `hatchling` as the build backend. uv ships its own first-party build backend (`uv_build`) that is faster, requires zero extra dependencies, and is the natural fit for uv-managed projects.

Reference: https://docs.astral.sh/uv/concepts/build-backend/

Files to update:
- `pyproject.toml` (root)
- `projects/flet-basics/pyproject.toml`
- `projects/flet-chat/pyproject.toml`
- `projects/flet-declarative/pyproject.toml`
- `projects/flet-todo/pyproject.toml`

For each file, replace:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/..."]  
```
with:
```toml
[build-system]
requires = ["uv_build>=0.7.4,<0.8"]
build-backend = "uv_build"
```
Note: uv_build auto-discovers `src/` layout packages — the explicit `[tool.hatch.build.targets.wheel]` section is not needed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Root `pyproject.toml` `[build-system]` uses `uv_build` and `[tool.hatch.*]` section removed
- [ ] #2 All workspace member `pyproject.toml` files updated to `uv_build`
- [ ] #3 `uv sync` from repo root succeeds with the new build backend
- [ ] #4 `uv build` succeeds for the root package and at least one workspace member
- [ ] #5 Imports from `src/notebooks` still resolve correctly in the shared `.venv` after the switch
<!-- AC:END -->
