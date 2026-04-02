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

## General Preferences

- Be concise and direct in responses
- Use markdown formatting for clarity
- When working with Git, only commit when explicitly asked
- Use `/init` command output to understand project structure
