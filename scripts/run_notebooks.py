#!/usr/bin/env python3
"""Run Jupyter notebooks in-place using papermill.

Usage:
    # Run a single notebook (output overwrites input):
    python scripts/run_notebooks.py notebooks/deep/07-language-modeling.ipynb

    # Run all notebooks in a folder:
    python scripts/run_notebooks.py notebooks/deep/

    # Run all notebooks in a folder, continuing after failures:
    python scripts/run_notebooks.py notebooks/deep/ --no-fail-fast

    # Dry-run: show which notebooks would be executed without running them:
    python scripts/run_notebooks.py notebooks/deep/ --dry-run

    # Pass a specific kernel:
    python scripts/run_notebooks.py notebooks/deep/ --kernel python3
"""

import argparse
import sys
import time
from pathlib import Path


def find_notebooks(target: Path) -> list[Path]:
    """Return notebook paths for a file or folder target."""
    if target.is_file():
        if target.suffix != ".ipynb":
            print(f"Error: {target} is not a .ipynb file", file=sys.stderr)
            sys.exit(1)
        return [target]
    elif target.is_dir():
        notebooks = sorted(target.glob("*.ipynb"))
        # Exclude index notebooks
        notebooks = [n for n in notebooks if n.name != "index.ipynb"]
        return notebooks
    else:
        print(f"Error: {target} does not exist", file=sys.stderr)
        sys.exit(1)


def normalize_notebook(path: Path) -> None:
    """Add missing cell ids and normalize nbformat in-place."""
    import nbformat
    from nbformat.validator import normalize

    with open(path) as f:
        nb = nbformat.read(f, as_version=4)
    _, nb = normalize(nb)
    with open(path, "w") as f:
        nbformat.write(nb, f)


def run_notebook(path: Path, kernel: str, timeout: int) -> tuple[bool, float]:
    """Normalize then execute a notebook in-place. Returns (success, elapsed_seconds)."""
    import papermill as pm

    normalize_notebook(path)
    start = time.time()
    try:
        pm.execute_notebook(
            str(path),
            str(path),
            kernel_name=kernel,
            execution_timeout=timeout,
            progress_bar=False,
        )
        elapsed = time.time() - start
        return True, elapsed
    except Exception as exc:
        elapsed = time.time() - start
        print(f"\n  ERROR: {exc}", file=sys.stderr)
        return False, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Run Jupyter notebooks in-place with papermill."
    )
    parser.add_argument(
        "target",
        type=Path,
        help="Path to a .ipynb file or a folder containing notebooks.",
    )
    parser.add_argument(
        "--kernel",
        default="python3",
        help="Jupyter kernel name to use (default: python3).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-cell execution timeout in seconds (default: 600).",
    )
    parser.add_argument(
        "--no-fail-fast",
        action="store_true",
        help="Continue running remaining notebooks even if one fails.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print notebooks that would be executed without running them.",
    )
    parser.add_argument(
        "--normalize-only",
        action="store_true",
        help="Only normalize cell ids (fix MissingIDFieldWarning) without executing.",
    )
    args = parser.parse_args()

    notebooks = find_notebooks(args.target)

    if not notebooks:
        print("No notebooks found.")
        sys.exit(0)

    print(f"Found {len(notebooks)} notebook(s):")
    for nb in notebooks:
        print(f"  {nb}")

    if args.dry_run:
        print("\nDry run — nothing executed.")
        sys.exit(0)

    if args.normalize_only:
        import nbformat  # noqa: F401
        print()
        for nb in notebooks:
            print(f"Normalizing {nb} ...", end=" ", flush=True)
            normalize_notebook(nb)
            print("OK")
        sys.exit(0)

    try:
        import papermill  # noqa: F401
    except ImportError:
        print(
            "Error: papermill is not installed. Run: uv add papermill",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    results = []
    for nb in notebooks:
        print(f"Running {nb} ...", end=" ", flush=True)
        success, elapsed = run_notebook(nb, kernel=args.kernel, timeout=args.timeout)
        status = "OK" if success else "FAILED"
        print(f"{status} ({elapsed:.1f}s)")
        results.append((nb, success, elapsed))

        if not success and not args.no_fail_fast:
            print("\nStopping due to failure. Use --no-fail-fast to continue.")
            break

    print("\nSummary:")
    n_ok = sum(1 for _, ok, _ in results if ok)
    n_fail = len(results) - n_ok
    total = sum(e for _, _, e in results)
    for nb, ok, elapsed in results:
        mark = "✓" if ok else "✗"
        print(f"  {mark} {nb}  ({elapsed:.1f}s)")
    print(f"\n{n_ok} passed, {n_fail} failed, {total:.1f}s total")

    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
