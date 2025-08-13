# AI notebooks

Jupyter notebooks containing notes and implementation of AI models, algorithms, & applications.

<img src="./assets/ai.png">

## venv

The venv used to run the notebooks can be re-created easily using [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
make venv
```

You can also install requirements via `pip` entirely skipping `uv`:
```bash
make requirements
pip install -r requirements.txt
pip install -e .
```

:::{.callout-tip}
See [here](/topics/tooling/runpod.html) where we setup a remote environment from scratch.
:::

<!-- **NOTE:** You may have to add the `.venv` as ipykernel in JupyterLab:
```bash
uv add ipykernel
uv run python -m ipykernel install --user --name=ai-notebooks
``` -->


## the notebooks

The notebooks for each topic can be found in separate folders in the `/topics` directory:

| **Topic** | **Folder** | **Primary Reference(s)** |
| :-- | :-- | :-- |
| [Deep Learning](/topics/deep/) | `/deep` | [CMU 10-414/714: Deep Learning Systems](https://dlsyscourse.org/lectures/) (Fall 2022) |
