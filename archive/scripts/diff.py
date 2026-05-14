"""
CLI notebook diff viewer (inputs and outputs, cells with no diffs are skipped).
Opens static HTML in your browser; one page per changed .ipynb.

Usage:
  python -m diff <commit>
  python -m diff <commit1> <commit2>

Deps:
  pip install nbformat diff-match-patch
"""

import difflib
import html
import io
import json
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import nbformat
from diff_match_patch import diff_match_patch

# -------------------------------
# Git helpers
# -------------------------------


def run_git(args: List[str], text: bool = True) -> str:
    return subprocess.check_output(["git"] + args, text=text).strip()


def blob_at(commit: str, path: str) -> Optional[bytes]:
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"])
    except subprocess.CalledProcessError:
        return None


# -------------------------------
# Notebook -> cells (inputs + outputs)
# -------------------------------


def load_cells(nb_bytes: Optional[bytes]) -> List[Dict[str, Any]]:
    """
    Return list of cell dicts with id, type, source, and outputs.
    If nb_bytes is None, return empty list (file missing on that side).
    """
    if not nb_bytes:
        return []
    nb = nbformat.read(io.BytesIO(nb_bytes), as_version=4)
    cells = []
    for i, c in enumerate(nb.get("cells", []), start=1):
        if c.get("cell_type") not in {"code", "markdown"}:
            continue
        cell_data = {
            "id": c.get("id") or f"idx-{i}",
            "type": c["cell_type"],
            "source": str(c.get("source", "")).splitlines(),
            "outputs": [],
        }

        if c["cell_type"] == "code" and "outputs" in c:
            for output in c["outputs"]:
                output_data = {"output_type": output["output_type"]}
                if output["output_type"] == "stream":
                    output_data["text"] = output.get("text", "").splitlines()
                elif output["output_type"] in ["display_data", "execute_result"]:
                    output_data["data"] = output.get("data", {})
                    # Special handling for image outputs
                    if "image/png" in output.get("data", {}):
                        output_data["image/png"] = output["data"]["image/png"]
                    if "image/svg+xml" in output.get("data", {}):
                        output_data["image/svg+xml"] = output["data"]["image/svg+xml"]
                elif output["output_type"] == "error":
                    output_data.update(
                        {
                            "ename": output.get("ename", ""),
                            "evalue": output.get("evalue", ""),
                            "traceback": output.get("traceback", []),
                        }
                    )
                cell_data["outputs"].append(output_data)

        cells.append(cell_data)
    return cells


# -------------------------------
# Inline diff helpers
# -------------------------------

_dmp = diff_match_patch()


def escape(s: str) -> str:
    return html.escape(s, quote=False)


def inline_diff_html(a: str, b: str) -> Tuple[str, str]:
    """Character-level highlights between two strings."""
    diffs = _dmp.diff_main(a, b)
    _dmp.diff_cleanupSemantic(diffs)
    a_html, b_html = [], []
    for op, txt in diffs:
        safe = escape(txt)
        if op == 0:
            a_html.append(safe)
            b_html.append(safe)
        elif op == -1:  # delete
            a_html.append(f'<span class="diff-sub">{safe}</span>')
        elif op == 1:  # insert
            b_html.append(f'<span class="diff-add">{safe}</span>')
    return "".join(a_html), "".join(b_html)


# -------------------------------
# Output rendering
# -------------------------------


def render_output_diff(
    left_output: Dict[str, Any], right_output: Dict[str, Any]
) -> str:
    """Render side-by-side output comparison."""
    # Handle cases where one side is missing entirely
    if not left_output and not right_output:
        return ""

    left_type = left_output.get("output_type", "missing") if left_output else "missing"
    right_type = (
        right_output.get("output_type", "missing") if right_output else "missing"
    )

    if left_type != right_type:
        return _row(
            "",
            f"<em>Output type changed: {left_type}</em>",
            "",
            f"<em>Output type changed: {right_type}</em>",
            cls="chg",
        )

    if left_type == "stream":
        left_text = left_output.get("text", []) if left_output else []
        right_text = right_output.get("text", []) if right_output else []
        return render_cell_diff(
            "Output (stream)", left_text, right_text, context=2, is_output=True
        )

    elif left_type in ["display_data", "execute_result"]:
        left_data = left_output.get("data", {}) if left_output else {}
        right_data = right_output.get("data", {}) if right_output else {}

        # Handle image outputs
        if "image/png" in left_data or "image/png" in right_data:
            left_img = left_data.get("image/png")
            right_img = right_data.get("image/png")
            return _render_image_diff(left_img, right_img, "PNG")

        if "image/svg+xml" in left_data or "image/svg+xml" in right_data:
            left_svg = left_data.get("image/svg+xml")
            right_svg = right_data.get("image/svg+xml")
            return _render_image_diff(left_svg, right_svg, "SVG")

        # Compare text/plain representation if available
        if "text/plain" in left_data or "text/plain" in right_data:
            left_text = left_data.get("text/plain", "").splitlines()
            right_text = right_data.get("text/plain", "").splitlines()
            return render_cell_diff(
                "Output (text)", left_text, right_text, context=2, is_output=True
            )

        # Otherwise compare JSON representation
        left_json = json.dumps(left_data, indent=2).splitlines()
        right_json = json.dumps(right_data, indent=2).splitlines()
        return render_cell_diff(
            "Output (data)", left_json, right_json, context=2, is_output=True
        )

    elif left_type == "error":
        left_tb = "\n".join(left_output.get("traceback", [])) if left_output else ""
        right_tb = "\n".join(right_output.get("traceback", [])) if right_output else ""
        if left_tb == right_tb:
            return ""

        left_lines = left_tb.splitlines()
        right_lines = right_tb.splitlines()
        return render_cell_diff(
            "Error output", left_lines, right_lines, context=2, is_output=True
        )

    return ""


def _render_image_diff(
    left_img: Optional[str], right_img: Optional[str], img_type: str
) -> str:
    """Render side-by-side image comparison."""
    left_html = ""
    if left_img:
        if img_type == "PNG":
            left_html = f'<img src="data:image/png;base64,{left_img}" style="max-width:100%; max-height:300px;"/>'
        else:  # SVG
            left_html = f'<div style="max-width:100%; max-height:300px; overflow:auto;">{left_img}</div>'

    right_html = ""
    if right_img:
        if img_type == "PNG":
            right_html = f'<img src="data:image/png;base64,{right_img}" style="max-width:100%; max-height:300px;"/>'
        else:  # SVG
            right_html = f'<div style="max-width:100%; max-height:300px; overflow:auto;">{right_img}</div>'

    return f"""
<tr class="cell-header output"><td colspan="4">Output ({img_type} image)</td></tr>
<tr>
  <td class="lineno"></td><td class="code">{left_html or "<em>missing</em>"}</td>
  <td class="lineno"></td><td class="code">{right_html or "<em>missing</em>"}</td>
</tr>
"""


# -------------------------------
# Cell-level rendering with context
# -------------------------------


def render_cell_diff(
    title: str,
    left_lines: List[str],
    right_lines: List[str],
    context: int = 2,
    is_output: bool = False,
) -> str:
    """
    Side-by-side table rows for a single cell or output.
    Skips long equal runs, showing a compact placeholder with counts.
    """
    sm = difflib.SequenceMatcher(None, left_lines, right_lines)
    rows = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            block_len = i2 - i1
            if block_len <= 2 * context:
                for k in range(block_len):
                    s = escape(left_lines[i1 + k])
                    rows.append(_row(i1 + k + 1, s, j1 + k + 1, s, cls="eq"))
            else:
                # head context
                for k in range(context):
                    s = escape(left_lines[i1 + k])
                    rows.append(_row(i1 + k + 1, s, j1 + k + 1, s, cls="eq"))
                # gap
                hidden = block_len - 2 * context
                rows.append(_gap_row(hidden))
                # tail context
                for k in range(context):
                    s = escape(left_lines[i2 - context + k])
                    rows.append(
                        _row(i2 - context + k + 1, s, j2 - context + k + 1, s, cls="eq")
                    )
        elif tag == "replace":
            a_chunk = left_lines[i1:i2]
            b_chunk = right_lines[j1:j2]
            max_len = max(len(a_chunk), len(b_chunk))
            for idx in range(max_len):
                a_txt = a_chunk[idx] if idx < len(a_chunk) else ""
                b_txt = b_chunk[idx] if idx < len(b_chunk) else ""
                a_html, b_html = inline_diff_html(a_txt, b_txt)
                rows.append(
                    _row(
                        i1 + idx + 1 if idx < len(a_chunk) else "",
                        a_html,
                        j1 + idx + 1 if idx < len(b_chunk) else "",
                        b_html,
                        cls="chg",
                    )
                )
        elif tag == "delete":
            for k, a_txt in enumerate(left_lines[i1:i2]):
                rows.append(
                    _row(
                        i1 + k + 1,
                        f'<span class="diff-sub">{escape(a_txt)}</span>',
                        "",
                        "",
                        cls="sub",
                    )
                )
        elif tag == "insert":
            for k, b_txt in enumerate(right_lines[j1:j2]):
                rows.append(
                    _row(
                        "",
                        "",
                        j1 + k + 1,
                        f'<span class="diff-add">{escape(b_txt)}</span>',
                        cls="add",
                    )
                )

    # wrap in a section
    output_class = "output" if is_output else ""
    return f"""
<tr class="cell-header {output_class}"><td colspan="4">{escape(title)}</td></tr>
{''.join(rows)}
"""


def _row(ln_a, html_a, ln_b, html_b, cls=""):
    ln_a_disp = "" if ln_a == "" else str(ln_a)
    ln_b_disp = "" if ln_b == "" else str(ln_b)
    return f"""
<tr class="{cls}">
  <td class="lineno">{ln_a_disp}</td><td class="code">{html_a}</td>
  <td class="lineno">{ln_b_disp}</td><td class="code">{html_b}</td>
</tr>
"""


def _gap_row(n_hidden: int) -> str:
    return f"""
<tr class="gap">
  <td colspan="4">{n_hidden} unchanged lines hidden</td>
</tr>
"""


# -------------------------------
# Page assembly
# -------------------------------

PAGE_CSS = """
/* Base styles - high contrast dark mode */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background: #0d0d0d;
  color: #ffffff;
  margin: 0;
  line-height: 1.6;
  padding-bottom: 40px;
}

/* Top navigation bar */
.topbar {
  padding: 16px 20px;
  background: #000;
  border-bottom: 1px solid #404040;
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  gap: 16px;
  align-items: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
}

/* Buttons */
.btn {
  padding: 8px 20px;
  background: #1a1a1a;
  color: #fff;
  border-radius: 6px;
  text-decoration: none;
  border: 1px solid #606060;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:hover {
  background: #2d2d2d;
  border-color: #808080;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}

/* Table */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
  background: transparent;
}

/* Line numbers */
td.lineno {
  width: 4em;
  text-align: right;
  padding: 6px 10px;
  color: #b0b0b0;
  background: #000;
  font-family: 'SF Mono', 'Roboto Mono', Consolas, monospace;
  font-size: 13px;
  border-right: 1px solid #404040;
  position: sticky;
  left: 0;
  z-index: 2;
  user-select: none;
}

/* Right-side line numbers */
td.lineno + td + td.lineno {
  left: auto;
  right: 0;
  border-left: 1px solid #404040;
  border-right: none;
}

/* Code cells */
td.code {
  font-family: 'SF Mono', 'Roboto Mono', Consolas, monospace;
  font-size: 14px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 6px 10px;
  vertical-align: top;
  color: #fff;
  background: #0d0d0d;
  border-bottom: 1px solid #303030;
  transition: background 0.15s ease;
}

/* Diff highlights */
.diff-add {
  background: rgba(60, 160, 60, 0.25);
  color: #FFFFFF;
  padding: 2px 0;
  border-radius: 2px;
}

.diff-sub {
  background: rgba(200, 40, 40, 0.25);
  color: #FFFFFF;
  padding: 2px 0;
  border-radius: 2px;
}

/* Row highlights */
tr.sub td:nth-child(1),
tr.sub td:nth-child(2) {
  background: rgba(200, 40, 40, 0.12);
}

tr.add td:nth-child(3),
tr.add td:nth-child(4) {
  background: rgba(60, 160, 60, 0.12);
}

tr.chg td.code {
  background: rgba(255, 255, 0, 0.08);
}

/* Line number highlights */
tr.sub td.lineno:first-child {
  background: #330000;
  color: #ff7777;
  font-weight: bold;
}

tr.add td.lineno:last-child {
  background: #102810;
  color: #6ed46e;
  font-weight: bold;
}

tr.chg td.lineno {
  background: #333300;
  color: #ffff70;
  font-weight: bold;
}

/* Hover effects */
tr:not(.cell-header, .gap):hover td.code {
  background: #1a1a1a !important;
}

tr:not(.cell-header, .gap):hover td.lineno {
  background: #262626 !important;
}

/* Gap row */
tr.gap td {
  font-family: inherit;
  text-align: center;
  color: #808080;
  padding: 16px;
  background: #000;
  font-size: 13px;
  border-bottom: 1px solid #404040;
  font-style: italic;
}

/* Cell headers */
tr.cell-header td {
  font-family: inherit;
  background: #1a1a1a;
  color: #fff;
  font-weight: 700;
  padding: 14px 20px;
  font-size: 15px;
  border-bottom: 3px solid #0080ff;
  position: sticky;
  top: 65px;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

/* Output headers */
tr.cell-header.output td {
  border-bottom-color: #ff00ff;
  font-weight: 600;
  font-size: 14px;
}

/* Table header */
thead td {
  font-family: inherit;
  font-weight: 700;
  background: #000;
  padding: 16px 20px;
  font-size: 15px;
  border-bottom: 2px solid #606060;
  position: sticky;
  top: 65px;
  color: #fff;
}

/* Math */
.katex {
  color: #fff;
}

/* Images */
img {
  background: #fff;
  border: 2px solid #606060;
  border-radius: 4px;
  max-width: 100%;
  height: auto;
  margin: 8px 0;
}

/* Scrollbars */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-track {
  background: #000;
  border: 1px solid #303030;
}

::-webkit-scrollbar-thumb {
  background: #606060;
  border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
  background: #808080;
}

/* Responsive */
@media (max-width: 1200px) {
  td.lineno {
    width: 3em;
    padding: 4px 8px;
    font-size: 12px;
  }
  td.code {
    padding: 4px 10px;
    font-size: 13px;
  }
}

/* Equal rows */
tr.eq td.code {
  opacity: 1;
  color: #d0d0d0;
}
tr.eq:hover td.code {
  color: #fff;
}

/* Disabled buttons */
.btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* Toggle switch styles */
.toggle-container {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 12px;
}

.toggle-label {
    font-size: 14px;
    color: #b0b0b0;
    font-weight: 500;
}

.toggle-btn {
    position: relative;
    width: 50px;
    height: 24px;
    border-radius: 12px;
    background: #333;
    border: 1px solid #555;
    cursor: pointer;
    padding: 0;
    transition: all 0.3s ease;
}

.toggle-btn:hover {
    background: #3a3a3a;
}

.toggle-thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: #808080;
    border-radius: 50%;
    transition: all 0.3s ease;
}

/* On state */
.toggle-btn.active {
    background: #1a3a8a;
    border-color: #2d4d9a;
}

.toggle-btn.active .toggle-thumb {
    left: calc(100% - 22px);
    background: #ffffff;
}
"""


def make_page_html(
    notebook_path: str,
    left_label: str,
    right_label: str,
    cell_sections_html: str,
    prev_link: Optional[str],
    next_link: Optional[str],
) -> str:
    prev_btn = (
        f'<a href="{prev_link}" class="btn{" disabled" if not prev_link else ""}">⬅ Previous</a>'
        if prev_link is not None
        else '<a class="btn disabled">⬅ Previous</a>'
    )
    next_btn = (
        f'<a href="{next_link}" class="btn{" disabled" if not next_link else ""}">Next ➡</a>'
        if next_link is not None
        else '<a class="btn disabled">Next ➡</a>'
    )

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(notebook_path)} diff</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css"/>
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="topbar">{prev_btn} {next_btn} 
    <div class="toggle-container">
      <span class="toggle-label">KaTeX</span>
      <button class="toggle-btn" onclick="toggleMath()" id="renderBtn">
        <span class="toggle-thumb"></span>
      </button>
    </div>
  </div>
  <table>
    <thead><tr><td colspan="2">{html.escape(left_label)}</td><td colspan="2">{html.escape(right_label)}</td></tr></thead>
    <tbody id="contentArea">
      {cell_sections_html or '<tr class="gap"><td colspan="4">No changed input cells.</td></tr>'}
    </tbody>
  </table>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  <script>
  let isRendered = false;
  let originalContent = document.getElementById('contentArea').innerHTML;
  
  function renderMath() {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{left: "$$", right: "$$", display: true}},
        {{left: "$", right: "$", display: false}},
        {{left: "\\\\(", right: "\\\\)", display: false}},
        {{left: "\\\\[", right: "\\\\]", display: true}}
      ],
      throwOnError: false
    }});
    isRendered = true;
    document.getElementById('renderBtn').classList.add('active');
  }}
  
  function unrenderMath() {{
    // Restore original content
    document.getElementById('contentArea').innerHTML = originalContent;
    isRendered = false;
    document.getElementById('renderBtn').classList.remove('active');
  }}
  
  function toggleMath() {{
    if (isRendered) {{
      unrenderMath();
    }} else {{
      renderMath();
    }}
  }}
  
  function toggleMath() {{
    if (isRendered) {{
      unrenderMath();
    }} else {{
      renderMath();
    }}
  }}
  
  function tryClose() {{
    if (window.history.length === 1) {{
      window.close();
    }} else {{
      window.location = "about:blank";
    }}
  }}
  </script>
</body>
</html>"""


# -------------------------------
# CLI
# -------------------------------


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python -m nb_diff_tool <commit> [<commit2>]")
        sys.exit(1)

    base = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) == 3 else "HEAD"

    # list changed .ipynb paths between base and target
    files = run_git(["diff", "--name-only", base, target, "--", "*.ipynb"]).splitlines()
    if not files:
        print("No notebook diffs found.")
        return

    tmpdir = Path(tempfile.mkdtemp(prefix="nbdiff_"))

    pages = []
    for i, path in enumerate(files):
        left_blob = blob_at(base, path)
        right_blob = blob_at(target, path)

        left_cells = load_cells(left_blob)
        right_cells = load_cells(right_blob)

        # Align by index; label added/removed when one side missing
        max_len = max(len(left_cells), len(right_cells))
        sections = []
        for idx in range(max_len):
            lc = left_cells[idx] if idx < len(left_cells) else None
            rc = right_cells[idx] if idx < len(right_cells) else None

            if lc is None and rc is not None:
                # Inserted cell
                title = f"{path} — Cell {idx+1} [{rc['type']}] (added)"
                sections.append(render_cell_diff(title, [], rc["source"], context=2))
                # Add any outputs for new cell
                for o_idx, output in enumerate(rc["outputs"], 1):
                    sections.append(render_output_diff({}, output))
                continue
            if rc is None and lc is not None:
                # Removed cell
                title = f"{path} — Cell {idx+1} [{lc['type']}] (removed)"
                sections.append(render_cell_diff(title, lc["source"], [], context=2))
                # Add any outputs from removed cell
                for o_idx, output in enumerate(lc["outputs"], 1):
                    sections.append(render_output_diff(output, {}))
                continue

            # Both exist: check for differences
            cell_changed = False

            # Check source differences
            lines_l = lc["source"]
            lines_r = rc["source"]
            type_l = lc["type"]
            type_r = rc["type"]

            if (
                "\n".join(lines_l).strip() != "\n".join(lines_r).strip()
                or type_l != type_r
            ):
                title = (
                    f"{path} — Cell {idx+1} [{type_l}→{type_r}]"
                    if type_l != type_r
                    else f"{path} — Cell {idx+1} [{type_l}]"
                )
                sections.append(render_cell_diff(title, lines_l, lines_r, context=2))
                cell_changed = True

            # Check output differences
            left_outputs = lc.get("outputs", [])
            right_outputs = rc.get("outputs", [])

            # Compare outputs if either the cell changed or outputs differ in count
            if cell_changed or len(left_outputs) != len(right_outputs):
                max_outputs = max(len(left_outputs), len(right_outputs))
                for o_idx in range(max_outputs):
                    lo = left_outputs[o_idx] if o_idx < len(left_outputs) else {}
                    ro = right_outputs[o_idx] if o_idx < len(right_outputs) else {}
                    output_diff = render_output_diff(lo, ro)
                    if output_diff:
                        sections.append(output_diff)

        # Skip entire notebook if no changed cells or outputs remain
        if not sections:
            continue

        prev_link = f"{files[i-1].replace('/', '_')}.html" if i > 0 else None
        next_link = (
            f"{files[i+1].replace('/', '_')}.html" if i + 1 < len(files) else None
        )
        page_html = make_page_html(
            path, base, target, "".join(sections), prev_link, next_link
        )
        out = tmpdir / f"{path.replace('/', '_')}.html"
        out.write_text(page_html, encoding="utf-8")
        pages.append(out)

    if not pages:
        print("Only unchanged cells and outputs across changed notebooks.")
        return

    print(f"Opening {len(pages)} diff page(s) in {tmpdir} …")
    webbrowser.open(pages[0].as_uri())


if __name__ == "__main__":
    main()
