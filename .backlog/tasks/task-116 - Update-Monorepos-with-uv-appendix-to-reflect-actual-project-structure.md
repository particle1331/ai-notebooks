---
id: TASK-116
title: Update Monorepos with uv appendix to reflect actual project structure
status: To Do
assignee: []
created_date: '2026-06-09 10:39'
updated_date: '2026-06-09 11:39'
labels:
  - tooling
milestone: m-00
dependencies: []
priority: medium
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The appendix `## Appendix: Monorepos with uv` in `notebooks/tooling/01-runpod.ipynb` currently has a generic subsection `### ai-notebooks workspace structure` that was added as a placeholder. It needs to be updated to reflect the actual workspace state after TASK-2 and the projects/ registration task are complete.

Key points to emphasize:
- **Library vs application distinction**: the root project (`ai-notebooks`) is the library and notebook venv — it is not a workspace member, it IS the workspace root
- **Why separate workspaces for micro/demo/test apps**: isolation of app-specific deps (flet, flask, redis), cleaner root lockfile, ability to version and run apps independently, no pollution of the shared notebook venv with app deps
- **Actual members**: `flet-basics`, `flet-chat`, `flet-declarative`, `flet-todo` — what each does, what deps they own
- **Practical workflow**: how to add a dep to a member vs the root, how to run a member app

The updated subsection should serve as living documentation: a developer cloning the repo should understand the workspace structure and how to work with it from this section alone.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The `### ai-notebooks workspace structure` subsection updated with the real directory tree (all four flet members shown)
- [ ] #2 Prose clearly explains the library/application distinction — root = notebook venv + library, projects/* = isolated app workspaces
- [ ] #3 A callout or paragraph explains the benefit of workspace isolation for demo/test/micro apps (no dep pollution, independent versioning)
- [ ] #4 Workflow examples use real member names (flet-basics, flet-chat, etc.) not placeholder names
- [ ] #5 Section reads as current documentation, not aspirational — only reflects what is actually implemented
<!-- AC:END -->
