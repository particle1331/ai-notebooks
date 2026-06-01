---
id: TASK-117
title: Register all projects/ subdirectories as uv workspace members
status: To Do
assignee: []
created_date: '2026-06-09 10:39'
updated_date: '2026-06-09 11:39'
labels:
  - tooling
milestone: m-00
dependencies: []
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The `projects/` directory contains four Flet application projects, but only `flet-basics` is registered in `[tool.uv.workspace].members`. The others — `flet-chat`, `flet-declarative`, `flet-todo` — each have a `pyproject.toml` but are invisible to uv.

Current state of each unregistered project:
- `projects/flet-chat/` — has `pyproject.toml` but missing `[build-system]` section
- `projects/flet-declarative/` — has `pyproject.toml` but missing `[build-system]` section; has a `[dependency-groups] dev` with `flet[all]`
- `projects/flet-todo/` — has `pyproject.toml` with `flet[all]`, `flask`, `boto3`; no `[build-system]`

Also present but NOT packages:
- `projects/archived/` — two standalone scripts (`flet-s3-gallery`, `flet-vms`) with no `pyproject.toml`; leave as-is
- `projects/nbx/` and `projects/tpe-init/` — planning docs only, no code; leave as-is

All three projects should be added to `[tool.uv.workspace].members` and given a proper `[build-system]` section. The pinned `flet[all]` in `flet-declarative`'s dev deps should be cleaned up to match the pattern used by the other members.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `flet-chat`, `flet-declarative`, and `flet-todo` added to `[tool.uv.workspace].members` in root `pyproject.toml`
- [ ] #2 Each of the three projects has a valid `[build-system]` section (matching the pattern from `flet-basics`)
- [ ] #3 `flet-declarative` dependency-groups dev entry cleaned up — no duplicate/conflicting flet pin
- [ ] #4 `uv sync` from repo root resolves all four members without errors
- [ ] #5 Each member can be individually targeted: `uv run --package <name> python <script>` works for a script in each project
<!-- AC:END -->
