import json
from pathlib import Path
from string import Template

import nbformat
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs"
FEATURES_PATH = ROOT / "content" / "opisanie-priznakov.html"

SPRINTS = [
    (
        "Спринт 1",
        [
            ("notebooks/data_review.ipynb", "Обзор данных", "data_review.html"),
            ("notebooks/hbond_simple.ipynb", "Акцепторы и доноры", "hbond_simple.html"),
        ],
    ),
    ("Спринт 2", []),
]

KICKER = "Лабораторная работа 01"
TITLE = "Инфохимия. Статистический анализ свойств молекул"
INTRO = (
    "В работе по данным DrugBank разбирается, как устроены физико-химические "
    "свойства лекарственных молекул и какие из этих свойств можно считать "
    "случайными величинами. В наборе есть расчётные характеристики: размер "
    "молекулы, растворимость, способность образовывать водородные связи, "
    "кислотность и признаки того, насколько вещество похоже на лекарство. "
    "На первом спринте по этим данным смотрят распределения, связи между "
    "величинами и проверяют гипотезы. На втором из одной выбранной величины "
    "собирают генератор случайных чисел и сравнивают его с исходными данными. "
    "Слева собраны обзор всего набора, разбор акцепторов и доноров, описание "
    "столбцов и место для источников."
)

PAGE_STYLE = """
<style>
body { margin: 0; font-family: sans-serif; color: #222; background: #f6f6f6; }
.topbar { padding: 1.6rem 1.8rem; background: #fff; border-bottom: 1px solid #ddd; }
.kicker { margin: 0; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; color: #666; }
.topbar h1 { margin: 0.35rem 0 0; font-size: 2rem; line-height: 1.25; }
.layout { display: block; }
.sidebar {
    position: fixed;
    top: calc(50vh - 10rem);
    left: 1rem;
    width: 20rem;
    z-index: 5;
}
.sidebar a,
.sidebar a:hover { color: #222; text-decoration: none; }
.sidebar summary { display: block; list-style: none; cursor: pointer; }
.sidebar summary::-webkit-details-marker { display: none; }
.sidebar summary::marker { content: ""; }
.sidebar-box {
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    max-height: calc(100vh - 8rem);
    overflow: auto;
    padding: 0.7rem;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
}
.sidebar-box > a,
.sidebar-box > details { background: #fff; border: 1px solid #ddd; border-radius: 6px; }
.sidebar-box > a,
.sidebar-box > details > summary { display: block; padding: 0.8rem 1rem; border-radius: 6px; }
.sidebar-box > a:hover,
.sidebar-box > details > summary:hover { background: #eee; }
.sidebar details details { margin: 0.65rem 0.6rem; background: #fafafa; border: 1px solid #e4e4e4; border-radius: 6px; }
.sidebar details details > summary { display: block; padding: 0; border-radius: 6px; }
.sidebar details details > summary a { display: block; padding: 0.6rem 0.75rem; border-radius: 6px; }
.sidebar details details > summary a:hover { background: #eee; }
.notebook-item { position: relative; margin: 0.65rem 0.6rem; }
.notebook-link {
    display: block;
    margin: 0.65rem 0.6rem;
    padding: 0.6rem 0.75rem;
    border: 1px solid #e4e4e4;
    border-radius: 6px;
    background: #fafafa;
    color: #222;
}
.notebook-link:hover { background: #eee; }
.toc-pop .open-notebook { display: block; padding: 0.35rem 0.6rem; }
.sidebar .toc { margin: 0.2rem 0 0.4rem 1rem; padding: 0; list-style: none; }
.sidebar .empty { margin: 0.2rem 0.6rem 0.6rem; color: #777; font-size: 0.9rem; }
.content { margin-left: 22rem; margin-right: 22rem; min-width: 0; padding: 1.5rem 1rem 3rem 1rem; }
.panel { width: 100%; padding: 1.3rem 1.5rem; background: #fff; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
.panel h2 { margin: 0 0 0.8rem; font-size: 1.35rem; }
.lead { margin: 0; font-size: 1.05rem; line-height: 1.55; }
.panel table { width: 100%; border-collapse: collapse; margin-top: 0.4rem; }
.panel th, .panel td { padding: 0.55rem 0.7rem; border: 1px solid #ddd; text-align: left; vertical-align: top; }
.panel th { background: #f3f3f3; }
.panel td:first-child { font-family: monospace; white-space: nowrap; }
.code-fold { margin: 0.4rem 0 0.8rem; }
.code-fold > summary { cursor: pointer; }
.sidebar {
    font-family: sans-serif;
    font-size: 16px;
    font-weight: normal;
    line-height: 1.4;
}
.sidebar * {
    font-family: inherit;
    font-size: inherit;
    font-weight: inherit;
    line-height: inherit;
    letter-spacing: normal;
    box-sizing: border-box;
}
.sidebar a:link,
.sidebar a:visited,
.sidebar a:hover {
    color: #222;
    text-decoration: none;
}
</style>
"""

PAGE_SCRIPT = """
<script>
document.addEventListener("DOMContentLoaded", function () {
    var page = window.PAGE_CHROME;
    var bar = document.createElement("div");
    var layout = document.createElement("div");
    var aside = document.createElement("aside");
    var content = document.createElement("div");
    bar.className = "topbar";
    bar.innerHTML = "<p class=\\"kicker\\"></p><h1></h1>";
    bar.querySelector(".kicker").textContent = page.kicker;
    bar.querySelector("h1").textContent = page.title;
    layout.className = "layout";
    aside.className = "sidebar";
    aside.innerHTML = page.sidebar;
    content.className = "content";
    while (document.body.firstChild) {
        content.appendChild(document.body.firstChild);
    }
    layout.appendChild(aside);
    layout.appendChild(content);
    document.body.appendChild(bar);
    document.body.appendChild(layout);

    var areas = document.querySelectorAll(".jp-CodeCell .jp-InputArea, .code_cell .input_area");
    areas.forEach(function (area) {
        var details = document.createElement("details");
        var summary = document.createElement("summary");
        details.className = "code-fold";
        summary.textContent = "Код";
        area.parentNode.insertBefore(details, area);
        details.appendChild(summary);
        details.appendChild(area);
    });

    document.querySelectorAll(".notebook-item").forEach(function (item) {
        item.querySelector(".notebook-link").addEventListener("click", function () {
            var wasOpen = item.classList.contains("open");
            document.querySelectorAll(".notebook-item.open").forEach(function (other) {
                other.classList.remove("open");
            });
            if (!wasOpen) {
                item.classList.add("open");
            }
        });
        item.addEventListener("mouseleave", function () {
            item.classList.remove("open");
        });
    });

    var sidebar = document.querySelector(".sidebar");
    var baseTop = sidebar.getBoundingClientRect().top;
    function placeSidebar() {
        var limit = document.querySelector(".topbar").offsetHeight;
        var shift = Math.min(window.scrollY, limit);
        sidebar.style.top = (baseTop - shift) + "px";
    }
    window.addEventListener("scroll", placeSidebar);
    placeSidebar();
});
</script>
"""


def notebook_toc(notebook_path):
    notebook = nbformat.read(notebook_path, as_version=4)
    items = []
    pending_id = None
    for cell in notebook.cells:
        if cell.cell_type != "markdown":
            pending_id = None
            continue
        for line in cell.source.splitlines():
            stripped = line.strip()
            if stripped.startswith("<a id=") and stripped.endswith("</a>"):
                pending_id = stripped.split('"')[1]
                continue
            if not stripped.startswith("#"):
                pending_id = None
                continue
            marks = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[marks:].strip()
            anchor = pending_id
            pending_id = None
            if marks < 2 or marks > 3 or title == "Содержание" or not anchor:
                continue
            items.append((marks, title, anchor))
    return items


def toc_html(items, page_name):
    lines = ["<ul class=\"toc\">"]
    for level, title, anchor in items:
        offset = (level - 2) * 0.75
        lines.append(
            '<li style="margin-left: {offset}rem"><a href="{page}#{anchor}">{title}</a></li>'.format(
                offset=offset,
                page=page_name,
                anchor=anchor,
                title=title,
            )
        )
    lines.append("</ul>")
    return "\n".join(lines)


def sidebar_html():
    parts = ['<a href="index.html">О работе</a>']
    parts.append("<details><summary>Данные</summary>")
    parts.append(
        '<details><summary><a href="features.html">Описание признаков</a></summary></details>'
    )
    parts.append("</details>")
    for sprint_name, notebooks in SPRINTS:
        parts.append("<details><summary>{name}</summary>".format(name=sprint_name))
        if not notebooks:
            parts.append('<p class="empty">Ноутбуков пока нет</p>')
        for source, title, file_name in notebooks:
            parts.append(
                '<a class="notebook-link" href="{file}">{title}</a>'.format(
                    file=file_name,
                    title=title,
                )
            )
        parts.append("</details>")
    parts.append("</details>")
    parts.append("<details><summary>Материалы</summary>")
    parts.append(
        '<details><summary><a href="materials.html">Источники</a></summary></details>'
    )
    parts.append("</details>")
    return '<div class="sidebar-box">\n' + "\n".join(parts) + "\n</div>"


def chrome(html):
    payload = json.dumps(
        {"kicker": KICKER, "title": TITLE, "sidebar": sidebar_html()},
        ensure_ascii=False,
    )
    extra = PAGE_STYLE + "<script>window.PAGE_CHROME = " + payload + ";</script>" + PAGE_SCRIPT
    if "</body>" in html:
        return html.replace("</body>", extra + "</body>", 1)
    return html + extra


def notebook_to_html(notebook_path):
    notebook = nbformat.read(notebook_path, as_version=4)
    exporter = HTMLExporter()
    exporter.template_name = "classic"
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    html, _resources = exporter.from_notebook_node(notebook)
    return html


def write_simple_page(file_name, body):
    page = Template(
        """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>$title</title>
</head>
<body>
$body
</body>
</html>
"""
    ).substitute(title=TITLE, body=body)
    (OUTPUT_DIR / file_name).write_text(chrome(page), encoding="utf-8")


def write_notebook_pages():
    for _sprint_name, notebooks in SPRINTS:
        for source, _title, file_name in notebooks:
            html = notebook_to_html(ROOT / source)
            (OUTPUT_DIR / file_name).write_text(chrome(html), encoding="utf-8")


def write_index():
    body = (
        '<section class="panel">'
        "<h2>О работе</h2>"
        '<p class="lead">{intro}</p>'
        "</section>"
    ).format(intro=INTRO)
    write_simple_page("index.html", body)


def write_features():
    table = FEATURES_PATH.read_text(encoding="utf-8")
    body = (
        '<section class="panel">'
        "<h2>Описание признаков</h2>"
        "{table}"
        "</section>"
    ).format(table=table)
    write_simple_page("features.html", body)


def write_materials():
    body = (
        '<section class="panel">'
        "<h2>Источники</h2>"
        "<p>Пока пусто</p>"
        "</section>"
    )
    write_simple_page("materials.html", body)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    write_notebook_pages()
    write_index()
    write_features()
    write_materials()


if __name__ == "__main__":
    main()