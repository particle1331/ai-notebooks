# AI Assistant Preferences

## Notebook & Output Reading Policy

When reading Jupyter notebooks or files with outputs:

- **Check output length first** - don't blindly read massive outputs
- **Read small text outputs** (under ~1000 lines) - they're almost always useful for understanding code behavior
- **Skip large outputs** like:
  - SVG, PNG, binary data, plots, images
  - Docker build logs
  - Training epoch logs (hundreds of lines)
  - Very long error stack traces
  - Large data dumps
- **Focus on code cells and markdown explanations** - the actual logic and documentation
- If actual execution results are needed and outputs are too large, ask before reading or run the code yourself

This policy preserves token context while capturing the useful signal from text outputs.

## Notebook Cell References

Notebooks are referenced relative to the `notebooks/` directory (implied, not written).
The notation `path/to/notebook.ipynb:[N]` or `path/to/notebook.ipynb:[N,L1:L2]` refers to:
- `N` - the cell with current execution count N
- `L1:L2` - (optional) lines L1 to L2 within that cell's source (1-indexed)

Examples:
- `deep/03.ipynb:[50]` - the cell with execution count 50 in `notebooks/deep/03.ipynb`
- `deep/03.ipynb:[50,11:23]` - lines 11 to 23 of that cell

Always verify the cell content matches the user's description before acting on it. If the execution count appears stale (content doesn't match), ask the user to clarify.

## General Preferences

- Be concise and direct in responses
- Use markdown formatting for clarity
- When working with Git, only commit when explicitly asked
- Use `/init` command output to understand project structure
