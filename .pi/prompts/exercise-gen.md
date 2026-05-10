---
description: Generate exercise notebook from explanatory notebook
argument-hint: "<notebook-path> [difficulty] [hints]"
---

I need you to generate an exercise notebook from an explanatory notebook. Use the exercise generation pipeline.

**Input notebook:** $1 (the notebook path to convert)

**Output location:** `tmp/EXERCISE_$1` (preserve the original filename with EXERCISE_ prefix)

**Task:**
1. Load the notebook from the given path
2. **Add a header cell** at the beginning of the notebook:
   - Cell 0 (markdown): `# EXERCISE: <Original Title> [Difficulty: $2] [Hints: $3]`
3. Classify each code cell into one of four roles: setup, implementation, visualization, or utility
4. Transform each implementation cell into a TODO-scaffolded exercise version where:
   - Function/class signatures, docstrings, imports stay intact
   - Function bodies become `# TODO: implement` with `raise NotImplementedError`
   - Non-trivial blocks become `# TODO: <description>`
5. Keep all other cells (setup, visualization, utility) unchanged with outputs cleared
6. **Transform markdown cells** for VS Code readability:
   - Strip all Quarto-specific syntax: cell directives (`#| ...`), callout blocks (`:::{.callout-...}` ... `:::`), cross-reference labels, raw blocks, and any other Quarto extensions — convert to plain GitHub-flavored markdown
   - Condense each markdown cell: keep section headings, key equations/formulas (LaTeX), and core concepts; remove verbose prose explanations, examples that are re-implemented in code cells, and instructor commentary
   - The resulting markdown should serve as a compact reference (cheat sheet), not a tutorial
   - If a markdown cell has no headings, equations, or concepts worth keeping, drop it entirely
7. Write the output notebook to `tmp/EXERCISE_<original_filename>.ipynb`

**Difficulty level:** $2 (default: medium)
- easy: leave variable names and helper call names as hints
- medium: remove helper call names but keep structure
- hard: minimal scaffolding, only signature and docstring

**Include hints:** $3 (default: false)
- If true, insert a collapsible hint cell after each exercise cell using HTML `<details>`/`<summary>` tags, which VS Code renders as a clickable disclosure widget in markdown cells:

```
<details>
<summary>Hint</summary>

```text
<pseudocode>
```

</details>
```

Print a summary showing:
- Original notebook title
- Difficulty level: $2
- Hints included: $3
- Total cells in notebook
- Number of implementation cells converted
- Number of hints injected
- Output path
