---
name: matplotlib-style
description: >
  Matplotlib and seaborn plotting conventions extracted from 134 plotting cells
  across the ai-notebooks project. Covers figure creation, color palettes,
  axis styling, annotations, multi-panel layouts, and Quarto integration.
  Load this skill when creating or reviewing any visualization code.
---

# Matplotlib Style Guide

Extracted from 134 plotting cells across `notebooks/deep/` (108 cells, 29 notebooks)
and `notebooks/llm/` (26 cells, 10 notebooks). These patterns represent 10+ years of
consistent usage. Follow them exactly.

---

## Output Format

**SVG is the default.** Every notebook configures SVG output. Use one of these at
the top of each notebook:

```python
# Preferred — programmatic (used in most newer notebooks)
from matplotlib_inline import backend_inline
backend_inline.set_matplotlib_formats("svg")

# Alternative — Jupyter magic (used in some earlier notebooks)
%config InlineBackend.figure_formats = ["svg"]
```

Use `"retina"` only for notebooks with many large raster images (e.g., optimizer
trajectory animations). Use `"png"` only when SVG rendering is too slow (e.g.,
thousands of scatter points during debugging).

```python
# Conditional format for debugging-heavy notebooks
MATPLOTLIB_FORMAT = "png" if DEBUG else "svg"
backend_inline.set_matplotlib_formats(MATPLOTLIB_FORMAT)
```

---

## Imports

```python
# Always
import matplotlib.pyplot as plt
import numpy as np

# Only when needed
import matplotlib.gridspec as gridspec              # complex layouts
import matplotlib.cm as cm                          # colormaps by name
import matplotlib.colors as mcolors                 # custom colormaps
from matplotlib.colors import LinearSegmentedColormap  # custom colormaps
from matplotlib.ticker import StrMethodFormatter    # tick formatting
from mpl_toolkits.mplot3d import Axes3D             # 3D plots

# Seaborn — only for distribution plots
import seaborn as sns
```

---

## Figure Creation

**Always specify `figsize`.** Never call `plt.figure()` without a size.

### Single-axis figures

```python
plt.figure(figsize=(5, 4))      # small standalone plot (loss curve, bar chart)
plt.figure(figsize=(5, 3))      # compact (training loss)
plt.figure(figsize=(6, 4))      # medium (decision boundary, comparison)
plt.figure(figsize=(8, 3))      # wide-short (time series)
plt.figure(figsize=(8, 5))      # wide-medium (prediction plots)
plt.figure(figsize=(10, 4))     # wide (RNN training curves, gradient norms)
```

### Subplots

```python
fig, ax = plt.subplots(1, 2, figsize=(8, 4))       # side-by-side pair
fig, ax = plt.subplots(1, 3, figsize=(8, 3))        # three-panel
fig, ax = plt.subplots(1, 4, figsize=(12, 4))       # four-panel row
fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)  # vertical stack
fig, ax = plt.subplots(2, 2, figsize=(12, 7))       # 2x2 grid
fig, ax = plt.subplots(2, 10, figsize=(12, 3))      # wide grid (autoencoder)
fig, ax = plt.subplots(3, 5, figsize=(6, 4.5))      # image grid
fig, ax = plt.subplots(4, 4)                          # square grid (predictions)
```

### Custom width/height ratios

```python
fig, ax = plt.subplots(1, 4, figsize=(12, 4),
    gridspec_kw={"width_ratios": [1, 1.5, 1.5, 1.5]})

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4),
    gridspec_kw={"height_ratios": [4, 1]})
```

### GridSpec (complex layouts)

```python
# Optimizer comparison: 2x2 with different row heights
fig = plt.figure(figsize=(12, 7))
gs = fig.add_gridspec(2, 2, height_ratios=[2, 1], hspace=0.45, wspace=0.3)
ax_top_left = fig.add_subplot(gs[0, 0])
ax_top_right = fig.add_subplot(gs[0, 1])
ax_bot_left = fig.add_subplot(gs[1, 0])
ax_bot_right = fig.add_subplot(gs[1, 1])

# Mixed 2D + 3D
fig = plt.figure(figsize=(10, 4))
gs = fig.add_gridspec(1, 2, width_ratios=[2, 1])
ax1 = fig.add_subplot(gs[0], projection="3d")
ax2 = fig.add_subplot(gs[1])
```

### Constrained layout

```python
fig, ax = plt.subplots(1, 1, figsize=(8, 4), layout="constrained")
fig = plt.figure(figsize=(12, 5), constrained_layout=True)
```

### Closing every figure

```python
# Always call tight_layout before show (unless using constrained_layout)
fig.tight_layout()
plt.show()

# For saved figures (llm/ tutorials)
fig.tight_layout()
plt.savefig("filename.png", dpi=150, bbox_inches="tight")
plt.show()
```

---

## Color Conventions

### Default: matplotlib cycle colors

The **`C0`, `C1`, `C2`, ...** cycle is the dominant pattern in `deep/` notebooks.
Use these for sequential series without semantic meaning:

```python
ax.plot(x, y1, color="C0", label="train")
ax.plot(x, y2, color="C1", label="test")
```

### Semantic named colors

Use named colors only when the color carries meaning:

| Color | Meaning |
|-------|---------|
| `"black"` or `"k"` | Reference lines, correct predictions, baselines |
| `"red"` | Errors, wrong predictions, gradient issues |
| `"gray"` / `"lightgray"` | Background, secondary, de-emphasized |
| `"tomato"` | Warm emphasis |

```python
# Conditional coloring for prediction correctness
color = "black" if pred == target else "red"
colors = ["black" if i == label else "lightgray" for i in range(10)]
```

### Material Design hex palette (llm/ tutorials)

For multi-metric dashboards and diagnostics plots, use this semantic palette:

```python
COLORS = {
    "blue":        "#2196F3",  # train loss, primary metric
    "red":         "#F44336",  # gradient norms, errors
    "green":       "#4CAF50",  # healthy indicators, grad/weight ratio
    "deep_orange": "#FF5722",  # eval loss markers
    "purple":      "#9C27B0",  # learning rate
    "orange":      "#FF9800",  # throughput, secondary metric
    "blue_grey":   "#607D8B",  # policy loss
    "grey":        "#aaaaaa",  # raw/background traces
}
```

### Custom colormaps

```python
# Two-color gradient
cm = LinearSegmentedColormap.from_list("", ["C0", "C1"], N=100)

# Diverging
cmap = LinearSegmentedColormap.from_list("custom", ["red", "white", "blue"])
```

### Standard colormaps used

`"viridis"`, `"Greys"`, `"gray"`, `"Reds"`, `"Blues"`, `"Greens"`,
`"tab10"`, `"inferno"`, `"RdYlGn"`, `"YlOrRd"`, `"spring"`, `"summer"`,
`"autumn"`, `"winter"`

---

## Line Styling

```python
# Primary emphasis
ax.plot(x, y, linewidth=2, color="C0")
ax.plot(x, y, lw=2.0, color="#2196F3")

# Standard
ax.plot(x, y, linewidth=1.5, color="C1")

# Secondary/background
ax.plot(x, y, lw=1.2, alpha=0.7, color="#aaaaaa")
ax.plot(x, y, lw=0.8, alpha=0.5, color="gray")    # raw traces

# Reference/threshold lines
ax.axhline(threshold, color="gray", linestyle="--", lw=0.8)
ax.axvline(step, color="k", linestyle="dashed", alpha=0.6)

# Linestyle keywords (always spelled out, not abbreviated)
linestyle="dashed"
linestyle="dotted"
linestyle="solid"
```

---

## Marker Styling

```python
# Scatter plots
plt.scatter(x, y, s=10, color="C0")                    # small points
plt.scatter(x, y, s=60, edgecolors="k", facecolors="none")  # hollow circles
ax.scatter(x, y, s=3, alpha=0.5)                        # dense cloud

# Line + marker (eval points in llm/ tutorials)
ax.plot(x, y, "o-", color="#FF5722", ms=4, label="eval")
ax.plot(x, y, "s-", ms=5, label="secondary")            # square markers
```

---

## Grid Styling

Two conventions exist. Use **dotted** for new notebooks:

```python
# Preferred (newer notebooks, deep/03+, llm/)
plt.grid(linestyle="dotted", alpha=0.6)
ax.grid(linestyle="dotted", alpha=0.6)
ax.grid(True, alpha=0.3)

# Legacy (deep/01-02)
plt.grid(alpha=0.6, linestyle="dashed")
```

---

## Axis Labels and Titles

```python
# Axis labels — LaTeX for math, plain for non-math
plt.xlabel("p"); plt.ylabel("loss")
ax.set_xlabel(r"$w_0$"); ax.set_ylabel(r"$w_1$")
ax.set_xlabel("Training Step")
ax.set_ylabel("Loss (log)")

# Titles — only for subplots, never for single-axis standalone plots
ax.set_title("Train Loss")
fig.suptitle("Training Diagnostics", fontsize=14, fontweight="bold")

# Compact set() for multiple properties
ax.set(title="Loss", xlabel="Step", ylabel="Value")
```

**Rule:** Single standalone figures get labels but no title (the preceding markdown
cell provides context). Multi-panel figures use `ax.set_title()` per panel and
optionally `fig.suptitle()`.

---

## Ticks and Spines

```python
# Image display — turn off axes entirely
ax.axis("off")
plt.axis("off")
ax.set_xticks([]); ax.set_yticks([])

# Equal aspect ratio (scatter, decision boundaries)
ax.axis("equal")
plt.gca().set_aspect("equal")

# Scientific notation for large step counts
ax.ticklabel_format(axis="x", style="sci", scilimits=(3, 3))

# Heatmap tick labels
ax.set_yticks(range(len(layers)))
ax.set_yticklabels(layers, fontsize=8)

# Invert y-axis for horizontal bar charts
ax.invert_yaxis()

# Custom tick formatting
from matplotlib.ticker import StrMethodFormatter
ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
```

**Spines are never explicitly modified.** Let matplotlib defaults handle them.

---

## Legends

```python
# Default placement (most common)
plt.legend()
ax.legend()

# With fontsize (8 is standard for dense plots)
ax.legend(fontsize=8)
ax.legend(fontsize=8, ncol=2)
plt.legend(fontsize=8)

# Explicit location
ax.legend(loc="lower right")
ax.legend(loc="lower right", fontsize=8)
ax.legend(loc="upper left")

# Framealpha for overlapping content
ax.legend(framealpha=1.0)

# External placement (rare, for many-series plots)
ax.legend(loc="upper center", bbox_to_anchor=(0.1, -0.10), ncol=5)
```

**Rule:** Labels are always set via `label=` in plot calls, never via
`plt.legend(handles, labels)`.

---

## Annotations

### Reference lines

```python
# Horizontal baseline/threshold
plt.axhline(math.log(10), label="random clf", color="k", linestyle="dashed")
ax.axhline(1.0, color="gray", linestyle="--", label="clip threshold")
ax.axhline(0.5, color="gray", linestyle="--", lw=0.8, label="random")

# Vertical markers (train/test split, fine-tuning start, warmup end)
plt.axvline(split_idx, linestyle="dashed", color="k")
ax.axvline(warmup_steps, color="gray", linestyle="--", lw=0.8,
           label=f"warmup ends (step {warmup_steps})")

# Horizontal bands (healthy range, saturation zones)
ax.axhspan(1e-3, 1e-2, alpha=0.15, color="green", label="healthy")
ax.axvspan(-5, -1.8, color="lightgray", label="|f'(x)| <= 0.1")
```

### Fill between (confidence/percentile bands)

```python
ax.fill_between(np.arange(len(u)), lower, upper, color=f"C{i}", alpha=0.3)
```

### Text annotations

```python
# On heatmaps/grids
ax.text(j, i, value, ha="center", va="center", color="black")

# On scatter/embedding plots
ax.text(x + offset, y + offset, label_str)

# Fallback text when data is missing
ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
```

### Colorbars

```python
plt.colorbar(scatter, ticks=range(10))
```

---

## Dual-Axis Plots (twinx)

Used for loss + accuracy on the same figure:

```python
fig, ax1 = plt.subplots(figsize=(8, 2.5))
ax2 = ax1.twinx()

ax1.plot(loss, color="blue", linewidth=2)
ax2.plot(accuracy, color="red", linewidth=2)

ax1.set_xlabel("Step")
ax1.set_ylabel("Loss")
ax2.set_ylabel("Accuracy")

ax1.yaxis.label.set_color("blue")
ax2.yaxis.label.set_color("red")
```

---

## Log-Scale Plots

```python
# Log y-axis (gradient norms, loss spanning orders of magnitude)
ax.semilogy(steps, values, color="#F44336", lw=1.5)
plt.yscale("log")

# Log x-axis (learning rate range test)
plt.semilogx(lrs, losses, color="#2196F3", lw=1.5)

# Custom log base
ax.set_xscale("log", base=2)
```

---

## Image Display

```python
# Single image
ax.imshow(img, cmap="gray")
ax.axis("off")

# Image grid
fig, ax = plt.subplots(3, 5, figsize=(6, 4.5))
for i in range(3):
    for j in range(5):
        ax[i, j].imshow(images[i*5+j], cmap="Greys")
        ax[i, j].axis("off")

# Heatmap with annotations
ax.imshow(matrix, cmap="RdYlGn", vmin=-5, vmax=-1)
for i in range(rows):
    for j in range(cols):
        ax.text(j, i, f"{matrix[i,j]:.1f}", ha="center", va="center")

# Nearest-neighbor interpolation for pixel-level display
matplotlib.rcParams["image.interpolation"] = "nearest"
```

---

## 3D Plots

```python
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(10, 5))
ax = fig.add_subplot(121, projection="3d")
ax.plot_surface(X, Y, Z, alpha=0.6, cmap="viridis")
ax.scatter(x, y, z, s=5, color="red")
ax.set_xlabel(r"$w_0$"); ax.set_ylabel(r"$w_1$"); ax.set_zlabel("Loss")
```

---

## Seaborn (Minimal Usage)

Only `sns.distplot()` for weight initialization distribution analysis:

```python
import seaborn as sns

sns.distplot(x.reshape(-1), color="C0", label="input")
sns.distplot(y.reshape(-1), color="C1", label="output")

# With axis targeting
sns.distplot(data, bins=50, ax=ax[k, i], label=f"Layer {j}", hist=False)
```

**No other seaborn functions are used.** No `sns.set_theme()`, no `sns.heatmap()`,
no style sheets. All styling is done through raw matplotlib.

---

## Quarto Integration

### Code-fold for visualization boilerplate

All plot cells that exist only to produce a figure (no side effects, no variable
definitions used later) should use `#| code-fold: true`:

```python
#| code-fold: true
import matplotlib.pyplot as plt
import numpy as np

eps = 1e-5
p = np.linspace(0 + eps, 1, 10000)
plt.figure(figsize=(5, 4))
plt.plot(p, -np.log(p), linewidth=2, label="-log(p)")
plt.grid(alpha=0.6, linestyle="dashed")
plt.xlabel("p"); plt.ylabel("loss")
plt.legend();
```

### Echo false for complex illustration-only cells

```python
#| echo: false
```

Use when the code is long/complex and only the figure matters to the reader.

### Figure cross-references (Quarto)

```python
#| label: fig-loss
#| fig-cap: "Training loss over epochs."
```

---

## Reusable Plot Function Pattern (llm/ tutorials)

For diagnostic/monitoring plots, define top-level functions:

```python
def plot_training_diagnostics(history, save_path=None):
    """Plot 2x2 training diagnostics grid."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    fig.suptitle("Training Diagnostics", fontsize=14, fontweight="bold")

    panels = [
        ("loss", "Train Loss", "#2196F3"),
        ("grad_norm", "Gradient Norm", "#F44336"),
        ("ratio", "Update Ratio", "#4CAF50"),
        ("lr", "Learning Rate", "#9C27B0"),
    ]

    for ax, (key, title, color) in zip(axes.flat, panels):
        ax.plot([m[key] for m in history], color=color, lw=1.5)
        ax.set_title(title)
        ax.set_xlabel("Step")
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
```

**Pattern:** Accept data + optional save path. Set `fig.suptitle()`. Iterate panels.
Call `tight_layout()`, optionally `savefig(dpi=150)`, then `show()`.

---

## rcParams (Rare)

Only used once (optimizer notebook `deep/04.ipynb`) for a specific look:

```python
plt.rcParams.update({
    "font.size": 7,
    "font.family": "monospace",
    "lines.linewidth": 1.0,
    "figure.dpi": 150,
    "figure.figsize": (5, 3),
})
```

**Do not apply global rcParams by default.** Use explicit per-figure settings.

---

## Semicolon Suppression

Always end the last plotting call with `;` to suppress matplotlib's return value
in notebook output:

```python
plt.legend();
plt.plot(x, y);
ax.set_title("Loss");
```

---

## Anti-Patterns (Do NOT Use)

- `plt.style.use("...")` — never used; all styling is explicit
- `sns.set_theme()` or `sns.set()` — never used
- `plt.figure()` without `figsize` — always specify size
- Spine manipulation (`ax.spines[...].set_visible()`) — never done
- `plt.title()` on standalone single-axis figures — use preceding markdown instead
- `plt.savefig()` without `dpi=150` — always set dpi when saving
- `fig.colorbar()` with default placement — always use explicit axis targeting
