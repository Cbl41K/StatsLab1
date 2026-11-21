"""Keep a single sec-1 anchor immediately before each ## heading in markdown cells."""
from __future__ import annotations

import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
ANCHOR_RE = re.compile(r'^\s*<a id="(sec-1-\d+)"></a>\s*$')


def clean_cell(source: str) -> str:
    lines = source.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("## ") and not line.strip().startswith("### "):
            # collect anchors immediately above
            j = len(out) - 1
            anchors: list[str] = []
            while j >= 0 and (out[j].strip() == "" or ANCHOR_RE.match(out[j])):
                if ANCHOR_RE.match(out[j]):
                    anchors.insert(0, out[j])
                    out.pop(j)
                elif out[j].strip() == "":
                    out.pop(j)
                j -= 1
            if anchors:
                out.append(anchors[-1])
                out.append("")
            out.append(line)
        else:
            out.append(line)
        i += 1
    return "\n".join(out)


def main() -> None:
    path = ROOT / "notebooks/generator_ecdf.ipynb"
    nb = nbformat.read(path, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            cell.source = clean_cell(cell.source)
    nbformat.write(nb, path)
    print("cleaned", path.name)


if __name__ == "__main__":
    main()