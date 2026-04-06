# AGENTS.md

This document provides guidelines for agentic coding systems and AI assistants working on the ai-notebooks project.

## Project Overview

**ai-notebooks** is a research-focused monorepo combining Jupyter notebooks documenting AI/ML topics with supporting Python utilities and Flet applications. The project emphasizes educational clarity and reproducible research over production code patterns.

- **Primary Language:** Python 3.13+
- **Notebook Framework:** Jupyter with Quarto web publishing
- **Package Manager:** `uv` (Astral's fast Python package manager)
- **Documentation:** Quarto-rendered website published to GitHub Pages
- **Structure:** Notebooks organized by topic (deep learning, LLMs, agents, apps, tooling)

## Build & Development Commands

### Environment Setup
```bash
make uv              # Install/verify uv package manager
make venv            # Create Python 3.13 venv and sync dependencies
make requirements    # Generate requirements.txt from pyproject.toml
```

### Documentation & Preview
```bash
make docs            # Preview documentation with quarto (http://localhost:4200)
```

### Running Code
```bash
jupyter notebook     # Launch Jupyter server (notebooks auto-discovered)
python -m notebook   # Alternative Jupyter launch
```

### Package Development
```bash
uv sync              # Sync dependencies from uv.lock
uv add <package>     # Add new dependency
uv remove <package>  # Remove dependency
```

## Testing & Validation

**Note:** This is a research/educational repository, not a production system.
- **No formal testing framework** is configured (no pytest, unittest, tox)
- **Notebooks serve as executable documentation** – validation occurs via cell execution
- **Manual testing approach:** Run cells to verify outputs match expected behavior
- **Code in src/notebooks/** should be validated through import and manual testing in notebooks

When modifying code, verify changes by:
1. Running affected notebook cells
2. Checking that expected outputs are produced
3. Running `make docs` to ensure documentation builds without errors

## Code Style & Standards

### Python Code Style

**Linting:** Ruff (configured in pyproject.toml)
```bash
ruff check .         # Run linter
ruff check --fix .   # Auto-fix style issues
```

**Configuration** (pyproject.toml):
- Ignores E731 (lambda assignment expressions allowed)
- Enforces PEP 8 standards otherwise
- No explicit formatter; uses Ruff defaults

**Naming Conventions:**
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Private/internal: prefix with `_`

### Imports

- Organize in three groups: stdlib → third-party → local (PEP 8 style)
- Prefer explicit imports: `from module import specific_item` over `import module`
- Use absolute imports; avoid relative imports in packages
- Group related imports together

### Type Hints

- Use type hints for function signatures in production code (src/ directory)
- Use standard types: `str`, `int`, `list[T]`, `dict[K, V]`, `tuple[...]`, `Optional[T]`
- Complex types: import from `typing` module if needed (Union, Callable, etc.)
- Notebooks can be more flexible with types; include hints in code cells for clarity

### Formatting & Whitespace

- **Line length:** 88 characters (Ruff default)
- **Indentation:** 4 spaces
- **Blank lines:** 2 between top-level definitions, 1 between methods
- Trailing whitespace: remove
- Use double quotes for strings (convention in this project)

### Error Handling

- Catch specific exceptions, not bare `except:`
- Use try/except/else/finally as appropriate
- Log errors with context using `rich` library when available
- In notebooks: display error context with clear explanations for debugging

### Documentation & Comments

- **Docstrings:** Use triple-quoted strings for functions, classes, modules
- **Comments:** Explain "why", not "what"; code should be self-explanatory
- **Notebooks:** Precede every code cell with markdown explaining intent (see notebook guidelines below)

## Jupyter Notebook Writing Standards

Notebooks in `notebooks/` follow structured pedagogical patterns:

### Structure
- **Title** + **Introduction** (1-3 paragraphs overview)
- **Sections** with theory followed by implementation
- **Optional appendices** for advanced topics

### Code Cell Conventions
- **Every cell preceded by descriptive markdown** explaining the cell's purpose
- Use **bold structural labels** (`**Data.**`, `**Model.**`, `**Training.**`, etc.) to organize cell content
- **Numbered annotations** (`# (1)`, `# (2)`) for comments on non-obvious lines

### Markdown & Prose
- **Action-first style:** "We compute X" rather than "Computing X is done"
- **Inline enumeration** for lists within sentences
- **Math:** Use inline LaTeX (`$...$`) for all quantities; display equations in `$$...$$` blocks
- **Emphasis:** Bold for technical terms and labels only; italics for informal usage
- **Callouts:** Use Quarto syntax:
  - `:::{.callout-note}` for enriching information
  - `:::{.callout-caution}` for pitfalls/warnings
  - `:::{.callout-important}` for hard constraints

### Cell References in Documentation
When referring to notebook cells in code or documentation, use:
- `path/to/notebook.ipynb:[N]` – cell with execution count N
- `path/to/notebook.ipynb:[N,L1:L2]` – lines L1-L2 within that cell

Examples:
- `deep/03.ipynb:[50]` – execution count 50 in notebooks/deep/03.ipynb
- `deep/03.ipynb:[50,11:23]` – lines 11-23 of that cell

### Output Handling
When reading notebooks:
- **Skip large outputs:** SVG, PNG, plots, binary data, training logs (>1000 lines)
- **Read small text outputs:** Model summaries, error messages, results tables
- **Focus on code cells:** The actual logic and logic explanations matter most

### Index Notebook Structure

The gold standard for index notebooks is `notebooks/apps/index.ipynb`. All series and sub-series index files must follow this structure exactly:

- **Cell 0:** `# Series Title` — title only, nothing else
- **Cell 1:** Single plain paragraph — the hook. No heading. Establishes stakes and context.
- **Cell 2:** `## About This Series` — with bold labels **Audience.**, **Stack.**, and a goal/project description. Use `[text]{.mark}` for 1–2 highlighted key phrases.
- **Cells 3–N:** One cell per part/section, each containing `## Part X. Name` (or `## Course Notebooks` for flat series) followed by a Quarto table. Table format rules:
  - `#` column: **plain text number** (e.g. `01`, `02`) — never a link
  - `Title` column: **linked title** (e.g. `[Notebook Title](/notebooks/path.html)`)
  - Table ends with `: {tbl-colwidths="[...]"}` on a new line
- **Final cell:** `## Prerequisites` and `## How to Read This Series` combined in one cell. "How to Read" uses 3–5 bolded `**If you...**` navigation entries.
- No trailing empty cells.
- Each cell's `"source"` is a single string (not a list of lines).

## Project-Specific Utilities

**src/notebooks/** provides helper modules:
- `agents.chat`: ChatHistory and ChatCompletions classes for LLM interactions
- `agents.tools`: Tool class for wrapping functions as callable tools
- `agents.utils`: Deployment utilities, HTML tag extraction

When enhancing these utilities, maintain backward compatibility and update docstrings.

## Temporary Files

When creating temporary files (e.g., patch scripts, one-off helper scripts, scratch files), always write them to the `tmp/` folder at the project root (i.e., `<project_root>/tmp/`), not the OS-level `/tmp/`. Never create temporary files elsewhere in the workspace unless they are meant to be committed.

## Git Workflow

- **Commit only when explicitly asked** by the user
- **Push only when explicitly requested**; do not push without user consent
- Create feature branches for significant changes
- Commit messages should be descriptive and reference issue numbers when applicable

## AI Assistant Preferences (from .github/AI_PREFERENCES.md)

When working on this repository:

1. **Notebook Output Policy:** Check output size before reading; skip large plots/logs; focus on code logic
2. **Cell Reference Format:** Use `notebook.ipynb:[N]` or `notebook.ipynb:[N,L1:L2]` notation
3. **Conciseness:** Be direct and concise in explanations
4. **Markdown:** Use GitHub-flavored markdown for formatting
5. **Project Structure:** Use `/init` command output to understand structure when needed

## Dependencies & Environment

**Python:** 3.13+

**Key Dependencies:**
- **ML/DL:** numpy, torch, torchvision, scikit-learn, matplotlib, seaborn
- **LLMs:** openai, langchain, langgraph, groq, dspy, ollama
- **Data:** pandas, datasets, boto3, chromadb
- **Dev:** jupyter, ipykernel, ipywidgets, nbdime
- **Utilities:** rich (for styled output), tqdm (progress bars), flet (UI apps)

**Installing Packages:**
```bash
uv add package_name    # Add and sync
uv sync                # Sync existing deps from lock file
```

## Quick Reference

| Task | Command |
|------|---------|
| Setup environment | `make venv` |
| Run notebooks | `jupyter notebook` |
| Preview docs | `make docs` |
| Check style | `ruff check .` |
| Fix style | `ruff check --fix .` |
| Add dependency | `uv add <package>` |

---

**Last Updated:** 2026-04-06  
**Project Root:** `/Users/particle1331/code/latest/ai-notebooks`
