---
name: notebook-writing-style
description: >
  Prose style and rhetorical conventions for notebook markdown cells. Covers
  voice, emphasis, mathematical rigor, concept introduction patterns, footnotes,
  links, and tables/figures. Load when writing or editing prose in Jupyter
  notebooks.
---

# Notebook Writing Style

For structural conventions (cell directives, callouts, cross-references, index
pages), see the `quarto-dev` skill instead.

---

## Prose Style

- **Action-first**: Lead with what to do. Prefer "To implement X: (1) ... and (2) ..." over "X is implemented by ...".
- **Inline enumeration**: Use "(1) ... and (2) ..." inline rather than a bulleted list. Reserve bullets for genuinely parallel items with no natural prose flow.
- **Concise openers**: Skip context-setting preambles. Get to the point immediately.
- **Minimal strong emphasis**: Bold is for key technical terms and structural labels only (see Emphasis section). Do not bold prohibitions or warnings inline.
- **Avoid redundancy**: Do not restate what was just shown in code. The sentence after a code block should add new information, draw a consequence, or set up the next block.
- **Counter-example before correct approach**: When eliminating an incorrect approach, state why it fails concisely before introducing the fix. "Note that $\phi$ linear doesn't work since we just get a linear classifier."

## Voice and Person

The default register is **impersonal and declarative** — the subject is the technical object, not the reader.

- **No "you"** in instructional prose. Acceptable only in rare hypothetical setups ("Suppose you want to classify...") or a brief aside in passing. Not the default.
- **No "the reader"** as a substitute for "you".
- **Minimal "we"**: At most once in a tight logical aside. Never as a narrative device ("we now turn to...").
- **Preferred alternatives**: Let the technical subject drive the sentence. Use `"Recall"`, `"Observe"`, `"Notice"` to direct attention. Use `"It turns out..."` for non-obvious results. Use passive constructions for derivation steps.

| Avoid                                     | Prefer                                     |
| ----------------------------------------- | ------------------------------------------ |
| "You can verify that the shapes match."   | "The shapes match by construction."        |
| "We now define the backward pass."        | "The backward pass is defined as follows:" |
| "You should use `float64` for gradcheck." | "`gradcheck` requires `float64` inputs."   |

: {tbl-colwidths="[50,50]"}

## Mathematical Rigor

- **Inline LaTeX** for any quantity, variable, set, or shape: $h_\Theta$, $\mathbb{R}^{d \times K}$, $\mathcal{L}$, $B$, $\tau$.
- **Display equations** (`$$...$$`) with `aligned` for multi-step derivations. Box final key results:
  ```latex
  $$\boxed{\Theta_{t+1} = \Theta_t - \frac{\alpha}{B}\,\mathbf{X}^\top(\hat{\mathbf{Y}} - \mathbf{Y})}$$
  ```
- **Shape annotations** embedded in equations via `\underbrace{...}_{d \times K}`.
- **Notation is defined inline** at point of first use, not deferred: "the **gradient** $\nabla_\Theta f(\Theta)$ is defined as the matrix of partial derivatives."
- **Cross-references** use Quarto syntax: `{#eq-label}` for equations, `@eq-label` for inline references, `[@Author2008]` for literature citations, `{#sec-label}` for appendix anchors.
- **Derivation commentary** follows each major algebraic step to justify shapes or operations: "For the second equation, the LHS has shape $(d, K)$, while the RHS has shape $(d, B) \times (B, K)$."
- Deeply theoretic claims (out of scope) are stated with citations or footnotes, not proved inline.

## Concepts Introduction

The large-scale pattern is **top-down** (problem context → structure → formalization), but locally **question-driven**: a problem is posed, then resolved.

- Open with a concrete scenario or motivating example before any math.
- Introduce the three-element structure of a learning algorithm (hypothesis class, loss, optimizer) as a table before writing any equations.
- Use `**Example.**` to ground abstract definitions in concrete instances with specific shapes/dimensions.
- Use counter-examples to eliminate bad approaches before introducing the correct one.

## Emphasis

**Bold** (`**...**`) — three uses only:

1. Key technical terms at first definition: `**cross-entropy loss**`, `**activation function**`, `**backward pass**`
2. Structural/rhetorical labels: `**Q.**`, `**Remark.**`, `**Example.**`, `**Demo.**`, `**NOTE:**`, `**Data.**`, `**Model.**`
3. Words central to an argument in running prose (not first use): `**test data**`, `**twice** the memory`

**Italics** (`*...*`) — two uses only:

1. Terms being named informally: `*language modeling*`, `*features*`, `*perplexity*`
2. Contrastive stress: "shuffle it _once_", "not _linearly_ separable"

**Backticks** — strict technical use: API objects, class names, method calls, code tokens, argument values. Never for emphasis.

**Quarto inline spans** for visual stress without hyperlinks:

- `[term]{.mark}` — yellow highlight for a key outcome term
- `[term]{.underline}` — underline for a term being defined or stressed in argument

## Footnotes

Use footnotes for — and only for — material that would bloat the prose:

1. Etymology or historical context for named terms
2. Precise mathematical qualifications too detailed for inline
3. Implementation alternatives mentioned but not pursued
4. Complexity heuristics offloaded from a main claim

## Links

- Wikipedia links for named mathematical objects at first use: `[Markovian assumption](https://en.wikipedia.org/wiki/Markov_model)`
- PyTorch docs links for referenced API objects: ``[`DataLoader`](https://docs.pytorch.org/...)``
- External course notes/papers for theoretical results stated without proof
- Internal Quarto links to other notebooks in the series: `[in here](/deep/03.html)` (i.e. `<folder>/<filename>` with `.ipynb` extension replaced by `.html`)

## Tables and Figures

- Prefer tables over bullet lists when content is parallel and comparative.
- Use `tbl-colwidths` for uneven columns, e.g., `{tbl-colwidths="[30,70]"}`.
- Figure captions open with a **bold title phrase** followed by a narrative explanation that describes the mechanism shown and connects it to the broader argument. Multi-sentence captions are normal. Example:
  > `![**SGD convergence to the minimum.** Although each step is only an approximation, the updates generally move in the correct direction...](./img/01-sgd.png){#fig-sgd}`
- Decorative figures with no cross-reference use raw `<img>` tags with no caption; a following `**Remark.**` cell provides the geometric interpretation.

## Code Cell Prose Conventions

Every code cell is preceded by at least a short sentence or bold label. Orphan code cells (no intro) do not appear.

- **Short terse intros** for routine steps: "Creating the data loader:", "Training the model:"
- **Bold structural labels** as mini-headers: `**Data.**`, `**Model.**`, `**Training.**`, `**Inference.**`
- **Post-code commentary** connects the output to the theory or sets up the next step. Never restates what the code does.

## Bad → Good

| Bad                                                                                                         | Good                                                                                   |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| "The mechanism is `F` — subclass it and implement two static methods:"                                      | "To implement custom autograd: (1) subclass `F` and (2) implement two static methods:" |
| "Call it with `F.apply(x)` — **never** instantiate directly."                                               | "This is then called with `F.apply(x)` instead of instantiating directly."             |
| "Every operation above uses PyTorch's built-in backward rules. Three situations require defining your own:" | Lead directly into the table.                                                          |
| "We now turn to the backward pass."                                                                         | "The backward pass is defined as follows:"                                             |
| "You can verify the shapes are correct."                                                                    | "The shapes are correct by construction."                                              |

: {tbl-colwidths="[50,50]"}
