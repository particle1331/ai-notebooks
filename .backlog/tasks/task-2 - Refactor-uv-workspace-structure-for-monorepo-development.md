---
id: TASK-2
title: Refactor uv workspace structure for monorepo development
status: In Progress
assignee: []
created_date: '2026-06-08 23:22'
updated_date: '2026-06-09 11:16'
labels: []
milestone: m-00
dependencies: []
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The workspace scaffolding is already partially in place — `[tool.uv.workspace]` exists in the root `pyproject.toml` and `projects/flet-basics` is already declared as a member. The remaining work is to clean up the root deps and verify the workspace is functional.

Current state:
- `flet[all]==0.80.1` still sits in the root `pyproject.toml` among notebook/library deps — it belongs only in the `flet-basics` member
- `projects/flet-basics/pyproject.toml` already declares `flet>=0.80.1` correctly
- `uv sync` has not been verified end-to-end since the workspace was partially set up

The fix is minimal: remove `flet` from root deps, verify `uv sync` resolves cleanly, and document the add-dep workflow in AGENTS.md.

**Workspace model (per `notebooks/tooling/01-runpod.ipynb` §Monorepos with uv):**
- Root = library + notebook venv (`src/notebooks/`, all ML/LLM/Jupyter deps)
- `projects/*` = application workspace members with only their own app-specific deps
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `flet[all]==0.80.1` removed from root `pyproject.toml` dependencies
- [ ] #2 `projects/flet-basics` remains listed under `[tool.uv.workspace] members` in the root `pyproject.toml`
- [ ] #3 `uv sync` from the repo root completes without errors and installs flet via the flet-basics member
- [ ] #4 Importing `flet` works in the shared `.venv` (i.e. the member is installed editably)
- [ ] #5 AGENTS.md Commands table gains a row for `uv add --package <member> <dep>` with a note on when to use it vs plain `uv add`
<!-- AC:END -->
