# nb_diff_tool.py
"""
CLI notebook diff viewer (inputs and outputs, cells with no diffs are skipped).
Opens static HTML in your browser; one page per changed .ipynb.

Usage:
  python -m nb_diff_tool <commit>
  python -m nb_diff_tool <commit1> <commit2>

Deps:
  pip install nbformat diff-match-patch
"""

import io
import sys
import html
import tempfile
import webbrowser
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import nbformat
from diff_match_patch import diff_match_patch
import difflib


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
            "outputs": []
        }
        
        if c["cell_type"] == "code" and "outputs" in c:
            for output in c["outputs"]:
                output_data = {"output_type": output["output_type"]}
                if output["output_type"] == "stream":
                    output_data["text"] = output.get("text", "").splitlines()
                elif output["output_type"] in ["display_data", "execute_result"]:
                    output_data["data"] = output.get("data", {})
                elif output["output_type"] == "error":
                    output_data.update({
                        "ename": output.get("ename", ""),
                        "evalue": output.get("evalue", ""),
                        "traceback": output.get("traceback", [])
                    })
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
        elif op == 1:   # insert
            b_html.append(f'<span class="diff-add">{safe}</span>')
    return "".join(a_html), "".join(b_html)


# -------------------------------
# Output rendering
# -------------------------------

def render_output_diff(left_output: Dict[str, Any], right_output: Dict[str, Any]) -> str:
    """Render side-by-side output comparison."""
    # Handle cases where one side is missing entirely
    if not left_output and not right_output:
        return ""
    
    left_type = left_output.get("output_type", "missing") if left_output else "missing"
    right_type = right_output.get("output_type", "missing") if right_output else "missing"
    
    if left_type != right_type:
        return _row("", f'<em>Output type changed: {left_type}</em>',
                   "", f'<em>Output type changed: {right_type}</em>',
                   cls="chg")
    
    if left_type == "stream":
        left_text = left_output.get("text", []) if left_output else []
        right_text = right_output.get("text", []) if right_output else []
        return render_cell_diff("Output (stream)", left_text, right_text, context=2, is_output=True)
    
    elif left_type in ["display_data", "execute_result"]:
        left_data = left_output.get("data", {}) if left_output else {}
        right_data = right_output.get("data", {}) if right_output else {}
        
        # Compare text/plain representation if available
        if "text/plain" in left_data or "text/plain" in right_data:
            left_text = left_data.get("text/plain", "").splitlines()
            right_text = right_data.get("text/plain", "").splitlines()
            return render_cell_diff("Output (text)", left_text, right_text, context=2, is_output=True)
        
        # Otherwise compare JSON representation
        left_json = json.dumps(left_data, indent=2).splitlines()
        right_json = json.dumps(right_data, indent=2).splitlines()
        return render_cell_diff("Output (data)", left_json, right_json, context=2, is_output=True)
    
    elif left_type == "error":
        left_tb = "\n".join(left_output.get("traceback", [])) if left_output else ""
        right_tb = "\n".join(right_output.get("traceback", [])) if right_output else ""
        if left_tb == right_tb:
            return ""
        
        left_lines = left_tb.splitlines()
        right_lines = right_tb.splitlines()
        return render_cell_diff("Error output", left_lines, right_lines, context=2, is_output=True)
    
    return ""


# -------------------------------
# Cell-level rendering with context
# -------------------------------

def render_cell_diff(title: str,
                    left_lines: List[str],
                    right_lines: List[str],
                    context: int = 2,
                    is_output: bool = False) -> str:
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
                    rows.append(_row(i2 - context + k + 1, s,
                                   j2 - context + k + 1, s, cls="eq"))
        elif tag == "replace":
            a_chunk = left_lines[i1:i2]
            b_chunk = right_lines[j1:j2]
            max_len = max(len(a_chunk), len(b_chunk))
            for idx in range(max_len):
                a_txt = a_chunk[idx] if idx < len(a_chunk) else ""
                b_txt = b_chunk[idx] if idx < len(b_chunk) else ""
                a_html, b_html = inline_diff_html(a_txt, b_txt)
                rows.append(_row(i1 + idx + 1 if idx < len(a_chunk) else "",
                               a_html,
                               j1 + idx + 1 if idx < len(b_chunk) else "",
                               b_html,
                               cls="chg"))
        elif tag == "delete":
            for k, a_txt in enumerate(left_lines[i1:i2]):
                rows.append(_row(i1 + k + 1, f'<span class="diff-sub">{escape(a_txt)}</span>',
                               "", "", cls="sub"))
        elif tag == "insert":
            for k, b_txt in enumerate(right_lines[j1:j2]):
                rows.append(_row("", "", j1 + k + 1,
                               f'<span class="diff-add">{escape(b_txt)}</span>',
                               cls="add"))
    
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
  <td colspan="4">… {n_hidden} unchanged lines …</td>
</tr>
"""


# -------------------------------
# Page assembly
# -------------------------------

PAGE_CSS = """
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
       background:#0b0f19; color:#e5e7eb; margin:0; }
.topbar { padding:10px; background:#0f172a; border-bottom:1px solid #1f2937; position:sticky; top:0; z-index:1;}
.btn { padding:6px 12px; background:#111827; color:#e5e7eb; border-radius:8px; text-decoration:none; border:1px solid #374151; }
.btn:hover { background:#0b1220; }
table { width:100%; border-collapse: collapse; }
td.lineno { width:4.5em; text-align:right; padding:4px; color:#9ca3af; border:1px solid #374151; background:#0f172a; }
td.code { white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; border:1px solid #374151; padding:6px; vertical-align: top; }
tr.eq td.code { background:#0c111c; }
.diff-add { background:#052e1b; }
.diff-sub { background:#3b0a0a; }
tr.add td.code { background:#081f14; }
tr.sub td.code { background:#1f0b0b; }
tr.chg td.code { background:#191300; }
tr.gap td { text-align:center; color:#9ca3af; border:1px dashed #374151; padding:6px; }
tr.cell-header td { background:#111827; color:#93c5fd; font-weight:600; border:1px solid #374151; padding:8px; }
tr.cell-header.output td { background:#1a1e2e; color:#a5b4fc; }
thead td { font-weight:700; background:#111827; border:1px solid #374151; padding:6px; }
.katex { color:#e5e7eb; }
"""

def make_page_html(
    notebook_path: str,
    left_label: str,
    right_label: str,
    cell_sections_html: str,
    next_link: Optional[str]
) -> str:
    nav = f'<a href="{next_link}" class="btn">Next ➡</a>' if next_link else ""
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(notebook_path)} diff</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css"/>
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="topbar">{nav} <button class="btn" onclick="renderMath()">Render KaTeX</button></div>
  <table>
    <thead><tr><td colspan="2">{html.escape(left_label)}</td><td colspan="2">{html.escape(right_label)}</td></tr></thead>
    <tbody>
      {cell_sections_html or '<tr class="gap"><td colspan="4">No changed input cells.</td></tr>'}
    </tbody>
  </table>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  <script>
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
            
            if "\n".join(lines_l).strip() != "\n".join(lines_r).strip() or type_l != type_r:
                title = f"{path} — Cell {idx+1} [{type_l}→{type_r}]" if type_l != type_r \
                        else f"{path} — Cell {idx+1} [{type_l}]"
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

        next_link = f"{files[i+1].replace('/', '_')}.html" if i + 1 < len(files) else None
        page_html = make_page_html(path, base, target, "".join(sections), next_link)
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