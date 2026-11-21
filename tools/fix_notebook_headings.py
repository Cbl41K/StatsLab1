"""Capitalize markdown headings in selected notebooks."""
from __future__ import annotations

import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent.parent

PATHS = [
    ROOT / "notebooks/cal_refractivity.ipynb",
    ROOT / "generators/lognormal_generator_(1).ipynb",
]


def _capitalize_title(title: str) -> str:
    title = re.sub(r"^##(\d)", r"## \1", title)
    if re.match(r"^\d+\.\s", title) and not re.match(r"^\d+\.\d+", title):
        title = re.sub(r"^(\d+)\.(?=\S)", r"\1. ", title)

    for i, ch in enumerate(title):
        if ch.isalpha():
            return title[:i] + ch.upper() + title[i + 1 :]
    return title


def fix_line(line: str) -> str:
    stripped = line.strip()
    if re.match(r"^####\s+\d+\.", stripped):
        stripped = "##" + stripped[4:]
        line = line[: len(line) - len(line.lstrip())] + stripped
    if not stripped.startswith("#"):
        return line
    marks = len(stripped) - len(stripped.lstrip("#"))
    if marks > 6:
        return line
    title = stripped[marks:].strip()
    if title.lower() == "содержание":
        return line
    if "random variables" in title.lower() or title.startswith("Generator:"):
        return line
    new_title = _capitalize_title(title)
    indent = line[: len(line) - len(line.lstrip())]
    return f"{indent}{'#' * marks} {new_title}"


def fix_notebook(path: Path) -> None:
    nb = nbformat.read(path, as_version=4)
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        cell.source = "\n".join(fix_line(line) for line in cell.source.splitlines())
    nbformat.write(nb, path)


def main() -> None:
    for path in PATHS:
        if path.is_file():
            fix_notebook(path)
            print("fixed headings:", path.relative_to(ROOT))


if __name__ == "__main__":
    main()