---
description: Generate exercise notebook from explanatory notebook
agent: ml-coding-expert
---

I need you to generate an exercise notebook from an explanatory notebook. Use the exercise generation pipeline.

**Input notebook:** $1 (the notebook path to convert)

**Output location:** `tmp/EXERCISE_$1` (preserve the original filename with EXERCISE_ prefix)

**Task:**
1. Load the notebook from the given path
2. Classify each code cell into one of four roles: setup, implementation, visualization, or utility
3. Transform each implementation cell into a TODO-scaffolded exercise version where:
   - Function/class signatures, docstrings, imports stay intact
   - Function bodies become `# TODO: implement` with `raise NotImplementedError`
   - Non-trivial blocks become `# TODO: <description>`
4. Keep all other cells (setup, visualization, utility, markdown) unchanged with outputs cleared
5. Write the output notebook to `tmp/EXERCISE_<original_filename>.ipynb`

**Difficulty level:** $2 (default: medium)
- easy: leave variable names and helper call names as hints
- medium: remove helper call names but keep structure
- hard: minimal scaffolding, only signature and docstring

**Include hints:** $3 (default: false)
- If true, insert collapsible pseudocode hint callouts after each exercise cell

Print a summary showing:
- Total cells in notebook
- Number of implementation cells converted
- Number of hints injected
- Output path

Use Claude to analyze cell content and generate the exercise transformations.
