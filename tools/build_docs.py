import json
import re
import shutil
from pathlib import Path
from string import Template

import nbformat
from nbconvert import HTMLExporter

from build_content import (
    AUTHORS,
    CAT_MARK_TABLE,
    DATA_NOTEBOOKS,
    EXTRA_MENU_NOTEBOOKS,
    FEATURES_PATH,
    INDEX_SECTIONS,
    INTRO,
    KICKER,
    OUTPUT_DIR,
    ROOT,
    SPRINTS,
    STATIC_IMAGES,
    TEAM,
    TITLE,
    guide_html,
)

TOOLS = Path(__file__).resolve().parent


def _page_style():
    css = (TOOLS / "page_style.css").read_text(encoding="utf-8")
    return "<style>\n" + css + "\n</style>\n"


def _page_script():
    js = (TOOLS / "page_script.js").read_text(encoding="utf-8")
    return "<script>\n" + js + "\n</script>\n"


PAGE_STYLE = _page_style()
PAGE_SCRIPT = _page_script()


def read_notebook(notebook_path):
    notebook = nbformat.read(notebook_path, as_version=4)
    _changes, notebook = nbformat.validator.normalize(notebook)
    return notebook


def notebook_toc(notebook_path):
    notebook = read_notebook(notebook_path)
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


def file_link(href, title, link_class="", byline_reveal=False):
    author = AUTHORS.get(href, "")
    byline = '<span class="byline">{author}</span>'.format(author=author) if author else ""
    classes = [c for c in (link_class, "byline-reveal" if byline_reveal else "") if c]
    class_attr = ' class="{}"'.format(" ".join(classes)) if classes else ""
    
    return '<a{class_attr} href="{href}">{title}{byline}</a>'.format(
        class_attr=class_attr,
        href=href,
        title=title,
        byline=byline,
    )


def feature_glossary():
    text = FEATURES_PATH.read_text(encoding="utf-8")
    glossary = {}
    pattern = re.compile(
        r"<tr><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td></tr>"
    )
    
    for name, description, kind in pattern.findall(text):
        glossary[name.strip()] = {
            "description": description.strip(),
            "kind": kind.strip(),
        }
    
    return glossary


def sidebar_html():
    parts = ['<a href="index.html">О работе</a>']
    parts.append('<details class="sidebar-nav-section" open><summary>Данные</summary>')
    parts.append('<div class="sidebar-nav-panel">')
    
    for _source, title, file_name in DATA_NOTEBOOKS:
        parts.append(file_link(file_name, title, "notebook-link"))
    
    parts.append(file_link("features.html", "Описание признаков", "notebook-link"))
    parts.append("</div></details>")
    
    for sprint_name, notebooks in SPRINTS:
        parts.append(
            '<details class="sidebar-nav-section" open><summary>{name}</summary>'.format(
                name=sprint_name
            )
        )
        
        parts.append('<div class="sidebar-nav-panel">')
        
        if not notebooks:
            parts.append('<p class="empty">Ноутбуков пока нет</p>')
        
        for _source, title, file_name in notebooks:
            parts.append(file_link(file_name, title, "notebook-link"))
        
        parts.append("</div></details>")
    
    for _source, title, file_name in EXTRA_MENU_NOTEBOOKS:
        parts.append(file_link(file_name, title, byline_reveal=True))
    
    parts.append(file_link("materials.html", "Источники"))
    
    return '<div class="sidebar-box">\n' + "\n".join(parts) + "\n</div>"


def chrome(html, sections, *, feature_lookup=True):
    payload = json.dumps(
        {
            "kicker": KICKER,
            "title": TITLE,
            "sidebar": sidebar_html(),
            "sections": sections,
            "featureLookup": feature_lookup,
            "featureGlossary": feature_glossary() if feature_lookup else {},
        },
        ensure_ascii=False,
    )
    
    extra = PAGE_STYLE + "<script>window.PAGE_CHROME = " + payload + ";</script>" + PAGE_SCRIPT
    boot = (
        "<script>(function(){try{if(localStorage.getItem('theme')!=='light')"
        "document.documentElement.setAttribute('data-theme','dark');}catch(e){}})();</script>"
    )
    
    head = html.lower().find("<head")
    
    if head != -1:
        close = html.find(">", head)
        
        if close != -1:
            html = html[: close + 1] + boot + html[close + 1 :]
    
    if "</body>" in html:
        return html.replace("</body>", extra + "</body>", 1)
    
    return boot + html + extra


def notebook_to_html(notebook_path):
    notebook = read_notebook(notebook_path)
    exporter = HTMLExporter()
    exporter.template_name = "classic"
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    html, _resources = exporter.from_notebook_node(notebook)
    return html


def write_simple_page(file_name, body, sections, *, feature_lookup=True):
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
    (OUTPUT_DIR / file_name).write_text(
        chrome(page, sections, feature_lookup=feature_lookup),
        encoding="utf-8",
    )


def page_sections(notebook_path):
    sections = []
    
    for _level, title, anchor in notebook_toc(notebook_path):
        sections.append({"title": title, "href": "#" + anchor})
    
    return sections


def write_notebook_pages():
    groups = [DATA_NOTEBOOKS, EXTRA_MENU_NOTEBOOKS]
    
    for _sprint_name, notebooks in SPRINTS:
        groups.append(notebooks)
    
    for notebooks in groups:
        for source, _title, file_name in notebooks:
            path = ROOT / source
            html = notebook_to_html(path)
            (OUTPUT_DIR / file_name).write_text(
                chrome(html, page_sections(path)),
                encoding="utf-8",
            )


def write_index():
    body = (
        '<section class="panel" id="vvedenie">'
        "<h2>Введение</h2>"
        '<div class="prose prose-intro">{intro}</div>'
        "</section>"
        '<section class="panel" id="poryadok">'
        "<h2>Порядок просмотра</h2>"
        "{guide}"
        "</section>"
        '<section class="panel" id="komanda">'
        "<h2>Команда</h2>"
        + TEAM
        + CAT_MARK_TABLE
        + "</section>"
    ).format(intro=INTRO, guide=guide_html())
    write_simple_page("index.html", body, INDEX_SECTIONS, feature_lookup=False)


def write_features():
    table = FEATURES_PATH.read_text(encoding="utf-8")
    body = (
        '<section class="panel">'
        "<h2>Описание признаков</h2>"
        "{table}"
        "</section>"
    ).format(table=table)
    write_simple_page("features.html", body, [])


def write_materials():
    body = (
        '<section class="panel">'
        "<h2>Источники</h2>"
        "<p>Список литературы появится здесь, когда его соберут.</p>"
        "</section>"
    )
    write_simple_page("materials.html", body, [])


def copy_static_images():
    if not STATIC_IMAGES.is_dir():
        return
    
    target = OUTPUT_DIR / "images"
    
    if target.exists():
        shutil.rmtree(target)
    
    shutil.copytree(STATIC_IMAGES, target)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    copy_static_images()
    write_notebook_pages()
    write_index()
    write_features()
    write_materials()


if __name__ == "__main__":
    main()
