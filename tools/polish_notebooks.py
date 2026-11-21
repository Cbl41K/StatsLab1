"""One-off fixes: anchors, Anna inspect cell, degenerating headings."""
from __future__ import annotations

import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent

ANCHOR_RE = re.compile(r'^\s*<a id="sec-1-\d+"></a>\s*$')


def dedupe_anchors(nb: nbformat.NotebookNode) -> None:
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.splitlines()
        kept: list[str] = []
        for line in lines:
            if ANCHOR_RE.match(line):
                if kept and ANCHOR_RE.match(kept[-1]):
                    continue
            kept.append(line)
        # drop runs of only anchors at cell start, keep last one before ##
        compact: list[str] = []
        anchor_buf: list[str] = []
        for line in kept:
            if ANCHOR_RE.match(line):
                anchor_buf.append(line)
                continue
            if anchor_buf:
                compact.extend(anchor_buf[-1:])
                anchor_buf = []
            compact.append(line)
        if anchor_buf and not compact:
            compact.extend(anchor_buf[-1:])
        cell.source = "\n".join(compact)


def remove_inspect_source_cell(nb: nbformat.NotebookNode) -> bool:
    removed = False
    new_cells = []
    for cell in nb.cells:
        if (
            cell.cell_type == "code"
            and "inspect.getsource(EmpiricalCDFGenerator)" in (cell.source or "")
        ):
            removed = True
            continue
        new_cells.append(cell)
    if removed:
        nb.cells = new_cells
    return removed


def promote_degenerating_headings(nb: nbformat.NotebookNode) -> None:
    inserted_intro = False
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        src = cell.source
        if not inserted_intro and src.startswith("Есть крайне интересное"):
            cell.source = (
                "## 1. Исследование распределения cal_pka_basic (KDE)\n\n" + src
            )
            inserted_intro = True
            continue
        src = src.replace("### Генератор\n", "## 2. Генератор смеси нормальных распределений\n", 1)
        src = src.replace(
            "### Общие выводы по работе генератора\n",
            "## 3. Общие выводы по первому генератору\n",
            1,
        )
        if src.startswith("Теперь перейдем к второму генератору"):
            src = "## 4. Генератор Ratio of Uniforms\n\n" + src
        if src.startswith("Тут в пору написать такой же завершающий"):
            src = "## 5. Общие выводы по второму генератору\n\n" + src
        cell.source = src

    if not any("## Содержание" in (c.source or "") for c in nb.cells if c.cell_type == "markdown"):
        first = nb.cells[0]
        if first.cell_type == "markdown" and not first.source.lstrip().startswith("#"):
            first.source = (
                "# Lab02 - sprint 2. Смесь для cal_pka_basic\n\n"
                "## Generator: degenerating / madness\n\n"
                + first.source
            )


def main() -> None:
    paths = [
        ROOT / "notebooks/generator_ecdf.ipynb",
        ROOT / "generators/generator.ipynb",
        ROOT / "notebooks/degenerating.ipynb",
    ]
    for path in paths:
        nb = nbformat.read(path, as_version=4)
        dedupe_anchors(nb)
        if path.name == "generator.ipynb":
            remove_inspect_source_cell(nb)
        if path.name == "degenerating.ipynb":
            promote_degenerating_headings(nb)
        nbformat.write(nb, path)
        print("polished", path.relative_to(ROOT))


if __name__ == "__main__":
    main()