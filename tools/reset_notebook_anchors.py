"""Strip sec-1 anchors and TOC shell, then re-apply notebook_format_shell."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
ANCHOR = re.compile(r'^\s*<a id="sec-1-\d+"></a>\s*$')


def strip_anchors_and_toc(path: Path) -> None:
    nb = nbformat.read(path, as_version=4)
    nb.cells = [
        c
        for c in nb.cells
        if not (c.cell_type == "markdown" and "Содержание" in (c.source or ""))
        and c.get("id") != "toc-shell"
        and c.get("id") != "doc-shell"
    ]
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        lines = [ln for ln in cell.source.splitlines() if not ANCHOR.match(ln)]
        cell.source = "\n".join(lines)
    nbformat.write(nb, path)


def main() -> None:
    names = sys.argv[1:] or [
        "notebooks/generator_ecdf.ipynb",
        "generators/generator.ipynb",
    ]
    shell = ROOT / "tools" / "notebook_format_shell.py"
    py = sys.executable
    for name in names:
        path = ROOT / name if "/" in name else ROOT / "notebooks" / name
        strip_anchors_and_toc(path)
        rel = path.relative_to(ROOT).as_posix()
        subprocess.check_call([py, str(shell), rel], cwd=ROOT)
        print("reset", rel)


if __name__ == "__main__":
    main()