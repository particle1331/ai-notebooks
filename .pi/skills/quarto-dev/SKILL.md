---
name: quarto-dev
description: >
  Quarto syntax and conventions for the ai-notebooks project. Covers code cell
  directives, callouts, cross-references, figures, tables, math rendering,
  span formatting, citations, index pages, and custom CSS. Load this skill when
  writing or reviewing any Quarto-rendered Jupyter notebook content.
---

# Quarto Conventions Reference

Extracted from the ai-notebooks project configuration and 68+ notebooks. These are
the actual patterns used -- follow them exactly.

---

## Project Configuration

All Quarto config is centralized in `_quarto.yml`. **Notebooks have no YAML
frontmatter.** Key settings:

```yaml
execute:
  freeze: auto # Only re-render changed notebooks

format:
  html:
    lightbox: true # Click-to-zoom images
    html-math-method: katex
    highlight-annotations: true # Enables # <N> annotations
    toc: true
    toc-location: right
    theme: united
    css: assets/styles.css

bibliography: assets/references.bib
```

---

## Code Cell Directives

All directives are `#|` comments at the **first lines** of a Python code cell.
They must appear before any code.

### `#| code-fold: true`

Collapses code by default; reader clicks to expand. Use for:

- Visualization/plotting cells (no side effects, no variable definitions used later)
- Setup boilerplate that's not pedagogically interesting

```python
#| code-fold: true
import matplotlib.pyplot as plt
import numpy as np

plt.figure(figsize=(5, 4))
plt.plot(x, y, linewidth=2)
plt.grid(linestyle="dotted", alpha=0.6)
plt.legend();
```

**Do NOT fold** cells that define variables, models, or functions used later.

### `#| echo: false`

Hides the code cell entirely; only output is shown. Use for:

- Warning suppression cells
- Utility imports that add noise
- Setup code the reader doesn't need to see

```python
#| echo: false
import warnings
warnings.filterwarnings("ignore")
```

### `#| output: false`

Hides cell output; code is shown. Use when the code is instructive but the
output is uninteresting or too long.

```python
#| output: false
model = train_model(config)  # training output suppressed
```

### `#| label: fig-<id>` and `#| fig-cap: "..."`

Labels a code cell's output as a cross-referenceable figure:

```python
#| label: fig-network-dag
#| fig-cap: "A computational graph of a two-layer neural network."
import graphviz
# ... plotting code ...
```

Referenced in markdown as `@fig-network-dag`.

---

## Numbered Annotations

Quarto's `highlight-annotations: true` enables the `# <N>` pattern. Place
numbered comments in code, then explain in the **following** markdown cell:

**Code cell:**

```python
class AddTensor(Tensor):
    def __init__(self, a: Tensor, b: Tensor):
        super().__init__(
            a.data + b.data,
            requires_grad=a.requires_grad or b.requires_grad,  # <1>
            parents=(a, b)
        )

    def _backward(self, parent) -> np.array:
        grad = self.grad                                    # <2>
        for _ in range(diff_ndim):                          # <3>
            grad = grad.sum(axis=0)
        return grad
```

**Following markdown cell:**

```markdown
1. Child nodes should also require grad for gradients to reach parent nodes.
2. Start with the upstream gradient $\frac{\partial \mathcal{L}}{\partial \mathbf{C}}$.
3. Sum out leftmost axis: $(3, 2, 5) \rightarrow (2, 5).$
```

---

## Callouts

Quarto fenced div syntax. Use **sparingly** -- typically 2-4 per notebook.
Place **after** the relevant discussion, not before. Keep brief (1-3 sentences).

### Types used in this project

```markdown
:::{.callout-note}
Enriching/supplementary information.
:::

:::{.callout-tip}
Practical advice or useful tricks.
:::

:::{.callout-caution}
Pitfalls, gotchas, things that will break.
:::

:::{.callout-warning}
Stronger warning than caution.
:::

:::{.callout-important}
Hard constraints the reader must follow.
:::
```

### With custom title

```markdown
:::{.callout-tip}

## Emergent behavior

Explanation text...
:::
```

### Collapsible

```markdown
:::{.callout-note collapse="false"}
Content here (expanded by default; reader can collapse).
:::
```

### Real examples

```markdown
:::{.callout-note}
Notice that the latter input is different from training data. In practice,
we want the models to perform well on unlabeled data.
In other words, the model **generalizes**.
:::
```

```markdown
:::{.callout-note}
We like to write this in the following slogan: $\text{UI} = f(\text{state}).$ Our goal
is to make the code simpler, more predictable, and easier to reason about.
:::
```

---

## Cross-References

### Figures

Define with either markdown syntax or code cell directive:

```markdown
![Caption text](img/llm-stats.png){#fig-llm-stats}
```

or:

```python
#| label: fig-network-dag
#| fig-cap: "Caption text."
```

Reference: `@fig-llm-stats` or `@fig-network-dag`

### Sections

Add ID to heading:

```markdown
## Appendix: Universal approximation {#sec-univapprox}
```

Reference within the same notebook: `@sec-univapprox`

### Links to Other Notebooks or Sections

Use standard markdown links with the rendered `.html` path. The URL structure
mirrors the source tree under `notebooks/`:

```markdown
[see here for STE introduction](/notebooks/deep/03.html#the-straight-through-estimator-ste)
```

- Path: `/notebooks/<section>/<file>.html`
- Fragment: `#<heading-slug>` (lowercase, spaces → hyphens, punctuation stripped)
- Link text: descriptive phrase, not a bare URL

**Linking to a notebook's top level** (no fragment):

```markdown
[Deep Learning Foundations](/notebooks/deep/index.html)
[Backpropagation notebook](/notebooks/deep/03.html)
```

**Linking to a specific section in another notebook:**

```markdown
[see the STE introduction](/notebooks/deep/03.html#the-straight-through-estimator-ste)
[gradient checkpointing](/notebooks/deep/05.html#gradient-checkpointing)
```

Always use `.html` rendered paths for cross-links. `.ipynb` paths are broken
in the rendered site.

### Equations

Add ID after display math:

```markdown
$$
\frac{\partial z}{\partial w} = \ldots
$$ {#eq-dzdw}
$$
```

Reference: `@eq-dzdw`

### Tables

Not currently used in this project, but the syntax is:

```markdown
| Col1 | Col2 |
| ---- | ---- |
| a    | b    |

: Caption {#tbl-id}
```

Reference: `@tbl-id`

---

## Figures

### Markdown syntax (most common)

```markdown
![](./img/01-1.png)
```

### With ID for cross-referencing

```markdown
![Caption text](img/llm-stats.png){#fig-llm-stats}
```

### Width control (percentage)

```markdown
![Caption](./img/brain-vat.png){#fig-brainvat width=70%}
```

### Width + alignment

```markdown
![Caption](./img/loss-landscape.png){#fig-02-loss fig-align="center" width=80%}
```

### Width in pixels

```markdown
![Caption](./img/imagenet.png){#fig-imagenet fig-align="center" width="500px"}
```

### Raw HTML (also used)

```html
<img src="./img/03-1.svg" width="60%" />
```

Use markdown syntax for new content. HTML `<img>` is acceptable for legacy
compatibility or when markdown syntax doesn't offer enough control.

### Figure captions

Captions are **full sentences** explaining the figure's purpose. Use bold
sub-labels for multi-part figures:

```markdown
![(**a**) Graph structure showing dependency. (**b**) Topological sorting result.](./img/03-compgraph.png)
```

---

## Tables

Standard markdown pipe tables with optional Quarto attributes:

```markdown
| Command | Description    |
| ------- | -------------- |
| `F2`    | Start Byobu    |
| `F6`    | Detach session |

: Byobu commands {tbl-colwidths="[30,70]"}
```

- `: Caption text` provides a table caption
- `{tbl-colwidths="[30,70]"}` controls column width proportions
- Tables are left-aligned (forced by `assets/styles.css`)

---

## Span Formatting

### Highlighted text (mark)

```markdown
[program]{.mark}
```

Renders with a highlight/background color. Use for key takeaways.

### Underlined text

```markdown
[*what*]{.underline}
```

Use for secondary emphasis on key phrases.

### Combined

```markdown
[[text]{.underline}]{.mark}
```

### Real examples

```markdown
**ML approach.** Collect a training set and feed these into a machine learning
algorithm, which will automatically produce a [program]{.mark} that solves this task.

The declarative approach means you describe [*what*]{.underline} the UI should look
like instead of [*how*]{.underline} to build the UI.

**NOTE:** (1) we use [`float64` inputs]{.mark} since finite differences
[need high precision]{.underline}.
```

---

## Citations

Uses BibTeX from `assets/references.bib`. Citation syntax:

### In text

```markdown
[@cot]
[@ReAct2023]
[@bottou2008tradeoffs]
```

### In headings

```markdown
### Chain-of-Thought [@cot]
```

### In figure descriptions

```markdown
**Figure 1 of** [@cot].
```

---

## Math Rendering (KaTeX)

Global setting: `html-math-method: katex`

### Inline

```markdown
where $d$ is the input dimensionality and $y_i \in [1, K]$
```

Use `$...$` for **all** mathematical quantities, even simple ones.

### Display

```markdown
$$
p_j = \frac{\exp(h_j(\mathbf{x}))}{\sum_l \exp(h_l(\mathbf{x}))}
$$
```

### With equation ID

```markdown
$$
\frac{\partial z}{\partial w} = \ldots
$$ {#eq-dzdw}
$$
```

### Boxed results

```markdown
$$
\boxed{
    \begin{aligned}
    \ell_{\text{CE}} &= -\log \text{Softmax}(h(\mathbf{x}))_y
    \end{aligned}
}
$$
```

### Common LaTeX commands used

| Category              | Commands                                                    |
| --------------------- | ----------------------------------------------------------- |
| Vectors/matrices      | `\mathbf{x}`, `\mathbf{W}`, `\boldsymbol{\theta}`           |
| Spaces/sets           | `\mathbb{R}^d`, `\mathcal{L}`, `\mathcal{D}`                |
| Operators             | `\text{Softmax}`, `\text{ReLU}`, `\operatorname{argmax}`    |
| Functions             | `h\colon \mathbb{R}^d \to \mathbb{R}^K`                     |
| Decorators            | `\hat{y}`, `\nabla`, `\partial`                             |
| Dimension annotations | `\underbrace{\mathbf{X}}_{\mathbb{R}^{M \times d}}`         |
| Derivations           | `\begin{aligned}...\end{aligned}` with `\\[0.75em]` spacing |
| Colored math          | `\color{4169E1}` (rare, for broadcasting distinction)       |

### Punctuation with math

- Period **inside** closing `$` when math ends a sentence: `$N = 60,000.$`
- Comma **outside** when sentence continues: `$\operatorname{argmax}_i h_i(\mathbf{x}) = y$, otherwise...`

---

## Footnotes

Standard Pandoc syntax:

```markdown
Some claim[^1] about a topic.

[^1]: Explanation or citation for the claim.
```

Use footnotes for tangential but useful information. Keep main prose focused.

---

## Video Embedding

HTML `<video>` tags for app demos (used in `notebooks/apps/`):

```html
<video
  src="./img/flet/greeting.mp4"
  autoplay
  loop
  muted
  controlslist="nodownload"
  oncontextmenu="return false"
  style="max-width:100%;"
></video>
```

No Quarto `{{< video >}}` shortcodes are used.

---

## HTML in Markdown Cells

| Pattern                     | Usage                                   |
| --------------------------- | --------------------------------------- |
| `<br>`                      | Vertical spacing between sections       |
| `&mdash;`                   | Em-dash character                       |
| `<!-- comment -->`          | Hidden content / commented-out sections |
| `<img src="..." width=...>` | Alternative to markdown image syntax    |
| `<video ...>`               | Video embedding                         |

---

## Index Notebook Structure

The gold standard for index notebooks is `notebooks/apps/index.ipynb`. All series
and sub-series index files must follow this structure exactly:

- **Cell 0:** `# Series Title` — title only, nothing else
- **Cell 1:** Single plain paragraph — the hook. No heading. Establishes stakes and context.
- **Cell 2:** `## About This Series` — with bold labels **Audience.**, **Stack.**, and a goal/project description. Use `[text]{.mark}` for 1–2 highlighted key phrases.
- **Cells 3–N:** One cell per part/section, each containing `## Part X. Name` (or `## Course Notebooks` for flat series) followed by a Quarto table. Table format rules:
  - `#` column: **plain text number** (e.g. `01`, `02`) — never a link
  - `#` column: **plain text number** for top-level series. Sub-series referenced from a parent index use a series prefix with colon separator: `NBX:01`, `CDA:01`, `DS:01`, `DD:01`.
  - `Title` column: **linked title** — plain descriptive text, no number prefix. Format: `[Notebook Title](/notebooks/path.html)`.
  - Table ends with `: {tbl-colwidths="[...]"}` on a new line
- **Final cell:** `## Prerequisites` and `## How to Read This Series` combined in one cell. "How to Read" uses 3–5 bolded `**If you...**` navigation entries.
- No trailing empty cells.
- Each cell's `"source"` is a single string (not a list of lines).

### Title Numbering in Index Tables

The `#` column of index tables carries the notebook number. This applies to all
series except `tooling/`.

**Within a series' own index** (e.g. `deep/index.ipynb`, `apps/cda/index.ipynb`),
the `#` column uses plain numbers:

- `| 01 | [Softmax Regression](01-softmax-regression.ipynb) | ... |`

**Sub-series referenced from a parent index** use a series prefix with colon separator:

- NBX (in `apps/index.ipynb`): `| NBX:01 | [Platform Architecture](/notebooks/apps/nbx/01-architecture.html) | ... |`
- CDA (in `apps/index.ipynb`): `| CDA:01 | [Streaming LLM Client](/notebooks/apps/cda/01-client.html) | ... |`
- DeepSeek (in `llm/index.ipynb`): `| DS:01 | [MLA & Mixture of Experts](/notebooks/llm/deepseek/01-deepseek-architecture.html) | ... |`
- Deep Dives (in `prep/index.ipynb`): `| DD:01 | [Advanced RAG](/notebooks/prep/deep-dives/01-advanced-rag.html) | ... |`

**Deep Dives in their own index** (`prep/deep-dives/index.ipynb`) also use the `DD:` prefix since that is their canonical numbering scheme.

---

## Sidebar / Navigation

Defined in `_quarto.yml`. Each section has a sidebar with glob auto-discovery:

```yaml
sidebar:
  - id: deep
    style: "floating"
    collapse-level: 2
    align: left
    contents:
      - section: ""
        href: notebooks/deep/index.ipynb
        contents: notebooks/deep/*.ipynb
```

Notebooks are ordered alphabetically by filename. The naming convention
(`01.ipynb`, `02.ipynb`, etc.) controls sidebar order.

The `agents` sidebar has two subsections (main + patterns subfolder):

```yaml
- id: agents
  contents:
    - section: ""
      href: notebooks/agents/index.ipynb
      contents: notebooks/agents/*.ipynb
    - section: ""
      href: notebooks/agents/patterns/index.ipynb
      contents: notebooks/agents/patterns/*.ipynb
```

### Sidebar Numbering

The Quarto sidebar `text:` entries in `_quarto.yml` carry the number prefix so the
sidebar is easy to scan. The format is `"NN. Title"` (zero-padded two digits, period,
space). This applies to all series except `tooling/`.

Examples:

- `- text: "01. Softmax Regression"`
- `- text: "13. Machine Translation"`

Sub-series entries within their parent sidebar section use plain numbers (the section
header like `"NBX: Compute Platform"` already provides context):

- `- text: "01. Platform Architecture"` (under `NBX: Compute Platform`)
- `- text: "01. Streaming LLM Client"` (under `CDA: Coding Agent From Scratch`)
- `- text: "01. MLA & Mixture of Experts"` (under `DeepSeek`)

Deep dives use bare paths (no explicit `text:`), so Quarto infers the title from
the notebook.

---

## Custom CSS (`assets/styles.css`)

Key rules that affect notebook rendering:

| Rule                                               | Effect                               |
| -------------------------------------------------- | ------------------------------------ |
| `body { text-align: justify; hyphens: auto; }`     | Justified text with auto-hyphenation |
| Tables: `margin-left: 0 !important`                | Left-aligned tables                  |
| Images: `max-width: 100%; filter: brightness(96%)` | Auto-sized, slightly dimmed          |
| Cell outputs: `border-radius: 4px`                 | Rounded corners on plot outputs      |

---

## Code Block Syntax (in markdown cells)

For standalone file code blocks (not executable cells):

````markdown
```{.python filename="src/main.py"}
def main():
    ...
```
````

For non-executable code examples:

````markdown
```python
# This is a code example, not an executable cell
model = GPT(config)
```
````

---

## Anti-Patterns (Do NOT Use)

- **Per-notebook YAML frontmatter** -- all config is in `_quarto.yml`
- **`{{< video >}}` shortcodes** -- use raw `<video>` HTML
- **Layout directives** (`:::{.panel}`, `:::{layout}`) -- not used in this project
- **`#| code-fold: true`** on cells that define variables used later
- **Multi-paragraph callouts** -- keep to 1-3 sentences
- **Callouts before the relevant discussion** -- always place after
- **`.ipynb` links in prose** -- always use `.html` rendered paths; `.ipynb` links are broken in the rendered site
