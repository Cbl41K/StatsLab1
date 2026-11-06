from pathlib import Path

import nbformat
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs"

NOTEBOOKS = [
    ("notebooks/data_review.ipynb", "Обзор данных", "data_review.html"),
    ("notebooks/hbond_simple.ipynb", "Акцепторы и доноры", "hbond_simple.html"),
]

PAGE_EXTRA = """
<style>
.site-nav {
    font-family: sans-serif;
    padding: 0.6rem 1rem;
    background: #f4f4f4;
    border-bottom: 1px solid #ddd;
}
.site-nav a {
    margin-right: 1rem;
}
.code-fold {
    margin: 0.4rem 0 0.8rem;
}
.code-fold > summary {
    cursor: pointer;
}
</style>
<script>
document.addEventListener("DOMContentLoaded", function () {
    var areas = document.querySelectorAll(
        ".jp-CodeCell .jp-InputArea, .code_cell .input_area"
    );
    areas.forEach(function (area) {
        var details = document.createElement("details");
        var summary = document.createElement("summary");
        details.className = "code-fold";
        summary.textContent = "Код";
        area.parentNode.insertBefore(details, area);
        details.appendChild(summary);
        details.appendChild(area);
    });
});
</script>
"""


def notebook_to_html(notebook_path):
    notebook = nbformat.read(notebook_path, as_version=4)
    exporter = HTMLExporter()
    exporter.template_name = "classic"
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    html, _resources = exporter.from_notebook_node(notebook)
    return html


def navigation_bar():
    links = ['<a href="index.html">Содержание</a>']
    for _source, title, file_name in NOTEBOOKS:
        links.append(f'<a href="{file_name}">{title}</a>')
    return '<div class="site-nav">' + "".join(links) + "</div>"


def insert_navigation(html):
    body_start = html.find("<body")
    if body_start == -1:
        return navigation_bar() + html
    body_tag_end = html.find(">", body_start) + 1
    return html[:body_tag_end] + navigation_bar() + html[body_tag_end:]


def insert_code_folding(html):
    if "</body>" not in html:
        return html + PAGE_EXTRA
    return html.replace("</body>", PAGE_EXTRA + "</body>", 1)


def write_notebook_pages():
    OUTPUT_DIR.mkdir(exist_ok=True)
    for source, _title, file_name in NOTEBOOKS:
        html = notebook_to_html(ROOT / source)
        html = insert_navigation(html)
        html = insert_code_folding(html)
        (OUTPUT_DIR / file_name).write_text(html, encoding="utf-8")


def write_index():
    cards = []
    for _source, title, file_name in NOTEBOOKS:
        cards.append(
            '<a class="card" href="{file_name}">{title}</a>'.format(
                file_name=file_name,
                title=title,
            )
        )
    page = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Lab01</title>
<style>
body {{
    margin: 0;
    font-family: sans-serif;
    background: #f6f6f6;
    color: #222;
}}
.page {{
    max-width: 40rem;
    margin: 4rem auto;
    padding: 0 1.5rem;
}}
h1 {{
    margin: 0 0 0.4rem;
    font-size: 2rem;
}}
.lead {{
    margin: 0 0 2rem;
    color: #555;
}}
.cards {{
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}}
.card {{
    display: block;
    padding: 1rem 1.2rem;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 6px;
    color: #222;
    text-decoration: none;
}}
.card:hover {{
    border-color: #888;
}}
</style>
</head>
<body>
<main class="page">
    <h1>Lab01</h1>
    <p class="lead">Материалы лабораторной работы</p>
    <nav class="cards">
{cards}
    </nav>
</main>
</body>
</html>
""".format(cards="\n".join(cards))
    (OUTPUT_DIR / "index.html").write_text(page, encoding="utf-8")


def main():
    write_notebook_pages()
    write_index()


if __name__ == "__main__":
    main()