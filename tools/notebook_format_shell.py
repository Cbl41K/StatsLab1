"""Add TOC, section anchors, and hidden code cells (hbond/logs pattern)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent


def _slug(text: str, fallback: str) -> str:
    t = text.lower()
    t = re.sub(r"[^\w\s\-]", "", t, flags=re.UNICODE)
    t = re.sub(r"\s+", "-", t.strip())
    return t[:48] if t else fallback


def hide_code_cells(nb: nbformat.NotebookNode) -> None:
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        meta = cell.setdefault("metadata", {})
        jupyter = meta.setdefault("jupyter", {})
        jupyter["source_hidden"] = True


def existing_anchor_ids(nb: nbformat.NotebookNode) -> set[str]:
    ids: set[str] = set()
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        for line in cell.source.splitlines():
            m = re.search(r'<a id="([^"]+)"', line)
            if m:
                ids.add(m.group(1))
    return ids


def collect_h2_sections(nb: nbformat.NotebookNode) -> list[tuple[str, str]]:
    """(title, anchor_id) for each ## heading without existing anchor on prev line."""
    items: list[tuple[str, str]] = []
    n = 0
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("## ") or stripped.startswith("### "):
                continue
            if i > 0 and '<a id="' in lines[i - 1]:
                continue
            title = stripped[3:].strip()
            n += 1
            anchor = f"sec-1-{n}"
            items.append((title, anchor))
    return items


def prepend_toc(
    nb: nbformat.NotebookNode,
    *,
    lab_title: str,
    doc_title: str,
    doc_anchor: str = "sec-1",
) -> None:
    if any("## Содержание" in (c.source or "") for c in nb.cells if c.cell_type == "markdown"):
        return

    sections = collect_h2_sections(nb)
    if not sections:
        return

    toc_lines = [
        lab_title,
        "",
        "## Содержание",
        "",
        f"**[{doc_title}](#{doc_anchor})**",
        "",
    ]
    for idx, (title, anchor) in enumerate(sections, start=1):
        short = re.sub(r"^шаг\s*\d+\.\s*", "", title, flags=re.I)
        short = re.sub(r"^\d+\.\s*", "", short)
        label = f"{idx}. {short}" if short else f"{idx}. {title}"
        toc_lines.append(f"- [{label}](#{anchor})")

    toc_cell = nbformat.v4.new_markdown_cell("\n".join(toc_lines))
    toc_cell["id"] = "toc-shell"
    nb.cells.insert(0, toc_cell)


def inject_doc_anchor(nb: nbformat.NotebookNode, doc_title: str) -> None:
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        if "## Содержание" in cell.source:
            continue
        if cell.source.lstrip().startswith("# ") and "<a id=" not in cell.source:
            body = cell.source
            cell.source = (
                '<a id="sec-1"></a>\n'
                f"## {doc_title}\n\n"
                + "\n".join(
                    line
                    for line in body.splitlines()
                    if not line.strip().startswith("# ")
                )
            )
            return


def inject_section_anchors(nb: nbformat.NotebookNode) -> None:
    known = existing_anchor_ids(nb)
    n = 0
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.splitlines()
        out: list[str] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            is_h2 = stripped.startswith("## ") and not stripped.startswith("### ")
            is_h3 = stripped.startswith("### ") and not stripped.startswith("#### ")
            is_h4 = stripped.startswith("#### ")
            if not (is_h2 or is_h3 or is_h4):
                out.append(line)
                continue
            if any('<a id="' in lines[j] for j in range(max(0, i - 3), i)):
                out.append(line)
                continue
            n += 1
            anchor = f"sec-1-{n}"
            while anchor in known:
                n += 1
                anchor = f"sec-1-{n}"
            known.add(anchor)
            out.append(f'<a id="{anchor}"></a>\n')
            out.append(line)
        cell.source = "\n".join(out)


NOTEBOOK_META = {
    "pka_basic_analysis.ipynb": {
        "lab_title": "# Lab01 - sprint 1. pKa (основной)",
        "doc_title": "Random Variables: cal_pka_basic",
    },
    "cal_refractivity.ipynb": {
        "lab_title": "# Lab01 - sprint 1. Молекулярная рефрактивность",
        "doc_title": "Random Variables: cal_refractivity",
    },
    "generator_ecdf.ipynb": {
        "lab_title": "# Lab02 - sprint 2. Генератор ЭФР",
        "doc_title": "Generator: ECDF для cal_pka_basic",
    },
    "degenerating.ipynb": {
        "lab_title": "# Lab02 - sprint 2. Смесь для cal_pka_basic",
        "doc_title": "Generator: degenerating / madness",
    },
    "generators/generator.ipynb": {
        "lab_title": "# Lab02 - sprint 2. Генератор ЭФР",
        "doc_title": "Generator: empirical CDF for A and D",
    },
    "generators/lognormal_generator_(1).ipynb": {
        "lab_title": "# Lab02 - sprint 2. Логнормальный генератор",
        "doc_title": "Generator: lognormal for cal_refractivity",
    },
}


def ensure_doc_anchor(nb: nbformat.NotebookNode, doc_title: str) -> None:
    if "sec-1" in existing_anchor_ids(nb):
        return
    idx = 0
    if nb.cells and "Содержание" in (nb.cells[0].source or ""):
        idx = 1
    cell = nbformat.v4.new_markdown_cell(
        f'<a id="sec-1"></a>\n\n## {doc_title}\n'
    )
    cell["id"] = "doc-shell"
    nb.cells.insert(idx, cell)


def format_notebook(path: Path) -> None:
    nb = nbformat.read(path, as_version=4)
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    meta = NOTEBOOK_META.get(rel) or NOTEBOOK_META.get(path.name)
    if not meta:
        raise ValueError(f"No meta for {path.name}")

    hide_code_cells(nb)
    inject_section_anchors(nb)
    inject_doc_anchor(nb, meta["doc_title"])
    prepend_toc(nb, **meta)
    ensure_doc_anchor(nb, meta["doc_title"])
    nbformat.write(nb, path)


def main(argv: list[str]) -> None:
    names = argv or list(NOTEBOOK_META.keys())
    for name in names:
        p = ROOT / name if "/" in name else ROOT / "notebooks" / name
        if not p.is_file():
            print("skip missing", name)
            continue
        format_notebook(p)
        print("formatted", name)


if __name__ == "__main__":
    main(sys.argv[1:])