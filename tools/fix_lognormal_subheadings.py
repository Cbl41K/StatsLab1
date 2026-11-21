"""Turn **N.N. Title** into ### headings in lognormal notebook."""
from __future__ import annotations

import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "generators/lognormal_generator_(1).ipynb"
SUB = re.compile(r"^\*\*(\d+\.\d+\..+?)\*\*\s*$", re.MULTILINE)


def main() -> None:
    nb = nbformat.read(PATH, as_version=4)
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        cell.source = SUB.sub(r"### \1", cell.source)
    nbformat.write(nb, PATH)
    print("updated subheadings in", PATH.name)


if __name__ == "__main__":
    main()