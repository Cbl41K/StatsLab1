import json
import re
from pathlib import Path
from string import Template

import shutil

import nbformat
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs"
STATIC_IMAGES = ROOT / "content" / "images"
FEATURES_PATH = ROOT / "content" / "opisanie-priznakov.html"

DATA_NOTEBOOKS = [
    ("notebooks/data_review.ipynb", "Обзор данных", "data_review.html"),
]

AUTHORS = {
    "features.html": "Сычев Александр | 467653",
    "data_review.html": "Сычев Александр | 467653",
    "hbond_simple.html": "Петрунина Анна | 327017",
    "logs_mw_ktvd.html": "Закликовский Иван | 503803",
    "generator_viz.html": "Закликовский Иван | 503803",
}

SPRINTS = [
    (
        "Спринт 1",
        [
            ("notebooks/hbond_simple.ipynb", "Акцепторы и доноры", "hbond_simple.html"),
            (
                "notebooks/logs_mw_ktvd.ipynb",
                "Растворимость и молекулярная масса",
                "logs_mw_ktvd.html",
            ),
        ],
    ),
    ("Спринт 2", []),
]

EXTRA_MENU_NOTEBOOKS = [
    (
        "notebooks/generator_viz.ipynb",
        "Визуализация генератора",
        "generator_viz.html",
    ),
]

INDEX_SECTIONS = [
    {"title": "Введение", "href": "#vvedenie"},
    {"title": "Порядок просмотра", "href": "#poryadok"},
    {"title": "Команда", "href": "#komanda"},
]

GUIDE_INTRO = "<p>Ниже — схема и развёрнутое описание порядка просмотра.</p>"

GUIDE_ROUTE = """
<ol class="route">
<li><div>
<h3>Обзор данных</h3>
<p>Основа. Сначала целиком проходят выборку: что в ней лежит, как она приведена к рабочему виду, какие распределения и связи видны до детальных разборов. Здесь же фиксируют цели и намечают, какие ветки пойдут в спринты.</p>
</div></li>
<li><div>
<h3>Описание признаков</h3>
<p>Дополнение. Короткая таблица: название признака и пояснение обычными словами. Открывать точечно, когда в тексте обзора непонятно, что за величина имеется в виду.</p>
</div></li>
<li><div>
<h3>Спринт 1</h3>
<p>Разбор выбранных пар величин уже после обзора, отдельный ноутбук на каждое направление.</p>
</div></li>
<li><div>
<h3>Спринт 2</h3>
<p>Создание генераторов (на основе базового генератора)соответствующих случайных величин, рассмотренных в предыдущем спринте, и сравнение с тем, что было в исходной выборке; дальнейшие выводы по выполенной работе.</p>
</div></li>
<li><div>
<h3>Визуализация генератора</h3>
<p>Доп. ветка. Отдельный раздел визуализации генератора(-ов). Уместен после обзора и параллельно со спринтами, когда уже ясна общая картина.</p>
</div></li>
<li><div>
<h3>Источники</h3>
<p>Справка. Хз - мб ссылка на датасет или чет типо того.</p>
</div></li>
</ol>
"""

GUIDE_FEATURE_HINT = """
<div class="route-feature-hint">
<p><strong>Примечание.</strong> На странице «Обзор данных» и в ноутбуках спринтов справа под оглавлением есть поиск признака: введите имя столбца из таблицы (например, <code>cal_logs</code>) — ниже появится его описание, без перехода на «Описание признаков», для удобства чтения - без многочисленных переходов между страницами.</p>
</div>
"""

GUIDE_SPRINT_NOTES = {
    "Спринт 1": "Разбор выбранных пар величин после обзора",
    "Спринт 2": "Генераторы случайных величин и сравнение с данными",
}

GUIDE_SPRINT_EXTRA = {
    "Спринт 2": {
        "heading": "Базовый генератор",
        "author": AUTHORS["data_review.html"],
        "file": "base_generator.py",
        "note_suffix": "начальный заданный генератор для остальных",
    },
}

GUIDE_SPRINT_LAYOUT = {
    "Спринт 1": {
        "left": 2,
        "right": 2,
        "bar": "thick",
        "wide": True,
        "stubs": True,
        "leaf_notes": False,
    },
    "Спринт 2": {
        "left": 2,
        "right": 1,
        "bar": "thick",
        "wide": True,
        "stubs": True,
        "stubs_only": True,
        "leaf_notes": False,
    },
}

GUIDE_NOTEBOOK_NOTES = {
    "data_review.html": "цели, очистка, распределения и план веток",
    "features.html": "словарь столбцов, открывать по ходу обзора",
    "materials.html": "статьи и описания, на которые опирается работа",
    "hbond_simple.html": "акцепторы и доноры водородной связи вместе",
    "logs_mw_ktvd.html": "растворимость и молекулярная масса в одном ноутбуке",
    "generator_viz.html": "как устроен и визуализируется генератор",
}


def guide_notebook_lists():
    s1 = [(href, title) for _src, title, href in SPRINTS[0][1]]
    s2 = [(href, title) for _src, title, href in SPRINTS[1][1]]
    extra_main = [(href, title) for _src, title, href in EXTRA_MENU_NOTEBOOKS]
    return s1, s2, extra_main


GUIDE_TRUNK_VBAR = (
    '<span class="tree-v2-vbar tree-v2-vbar--thin tree-v2-vbar--trunk" '
    'aria-hidden="true"></span>'
)


def guide_scheme_card(card_class, kicker="", title="", author="", note=""):
    bits = ['<div class="scheme-card {}">'.format(card_class)]
    if kicker:
        bits.append('<span class="scheme-kicker">{kicker}</span>'.format(kicker=kicker))
    if title:
        bits.append("<strong>{title}</strong>".format(title=title))
    if author:
        bits.append('<span class="scheme-author">{author}</span>'.format(author=author))
    if note:
        bits.append('<span class="scheme-note">{note}</span>'.format(note=note))
    bits.append("</div>")
    return "".join(bits)


def guide_leaf_card(href, title, *, show_note=True, stub=False):
    if stub or not title:
        return (
            '<div class="scheme-card scheme-card--leaf scheme-card--leaf-tbd">'
            '<span class="scheme-kicker">Ноутбук</span><strong>—</strong></div>'
        )
    note = GUIDE_NOTEBOOK_NOTES.get(href, "") if show_note else ""
    return guide_scheme_card(
        "scheme-card--leaf",
        title=title,
        author=AUTHORS.get(href, ""),
        note=note,
    )


def guide_slot_lists(left_n, right_n, notebooks, layout):
    items = list(notebooks)
    if layout.get("stubs_only"):
        items = []
    left, right = [], []
    fill_right_first = layout.get("fill_right_first")

    def fill_side(target, count, index):
        for _ in range(count):
            if index[0] < len(items):
                target.append(items[index[0]])
                index[0] += 1
            elif layout.get("stubs"):
                target.append(("", ""))

    index = [0]
    if fill_right_first:
        fill_side(right, right_n, index)
        fill_side(left, left_n, index)
    else:
        fill_side(left, left_n, index)
        fill_side(right, right_n, index)
    return left, right


def guide_leaf_row(side, href, title, layout):
    thick = layout["bar"] == "thick"
    bar_kind = "tree-v2-hbar--thick" if thick else "tree-v2-hbar--thin"
    bar = '<span class="tree-v2-hbar {kind}" aria-hidden="true"></span>'.format(
        kind=bar_kind
    )
    stub = not title
    card = guide_leaf_card(
        href,
        title,
        show_note=layout.get("leaf_notes", True),
        stub=stub,
    )
    if side == "left":
        return '<div class="tree-v2-leaf-row">{card}{bar}</div>'.format(card=card, bar=bar)
    return '<div class="tree-v2-leaf-row">{bar}{card}</div>'.format(card=card, bar=bar)


def guide_sprint_card(sprint_name, sprint_class):
    bits = ['<div class="scheme-card {}">'.format(sprint_class)]
    bits.append("<strong>{title}</strong>".format(title=sprint_name))
    note = GUIDE_SPRINT_NOTES.get(sprint_name, "")
    if note:
        bits.append('<span class="scheme-note">{note}</span>'.format(note=note))
    extra = GUIDE_SPRINT_EXTRA.get(sprint_name)
    if extra:
        bits.append('<div class="scheme-sprint-extra">')
        bits.append("<strong>{heading}</strong>".format(heading=extra["heading"]))
        if extra.get("author"):
            bits.append(
                '<span class="scheme-author">{author}</span>'.format(author=extra["author"])
            )
        if extra.get("file") and extra.get("note_suffix"):
            bits.append(
                '<span class="scheme-note">{file} - {suffix}</span>'.format(
                    file=extra["file"],
                    suffix=extra["note_suffix"],
                )
            )
        elif extra.get("note"):
            bits.append('<span class="scheme-note">{note}</span>'.format(note=extra["note"]))
        bits.append("</div>")
    bits.append("</div>")
    return "".join(bits)


def guide_sprint_block(sprint_name, notebooks, layout):
    sprint_class = "scheme-card--sprint"
    if layout.get("wide"):
        sprint_class += " scheme-card--sprint-wide"
    sprint_card = guide_sprint_card(sprint_name, sprint_class)
    left, right = guide_slot_lists(
        layout["left"], layout["right"], notebooks, layout
    )
    left_html = "\n".join(
        guide_leaf_row("left", href, title, layout) for href, title in left
    )
    right_html = "\n".join(
        guide_leaf_row("right", href, title, layout) for href, title in right
    )
    row_mod = " tree-v2-sprint-row--wide" if layout.get("wide") else ""
    return """
<div class="tree-v2-sprint">
  <div class="tree-v2-sprint-row{row_mod}">
    <div class="tree-v2-leaves tree-v2-leaves--left">{left}</div>
    <div class="tree-v2-sprint-mid">{sprint}</div>
    <div class="tree-v2-leaves tree-v2-leaves--right">{right}</div>
  </div>
</div>""".format(
        row_mod=row_mod,
        left=left_html,
        right=right_html,
        sprint=sprint_card,
    )


def guide_tree_html():
    main_href = DATA_NOTEBOOKS[0][2]
    s1_notebooks, s2_notebooks, extra_main = guide_notebook_lists()
    parts = [
        '<div class="tree-v2">',
        '<div class="tree-v2-root">',
        '<div class="tree-v2-side tree-v2-side--left">',
        guide_scheme_card(
            "scheme-card--ghost scheme-card--minor scheme-card--sources-compact",
            title="Источники",
        ),
        '<span class="tree-v2-hbar tree-v2-hbar--thin tree-v2-hbar--muted" aria-hidden="true"></span>',
        "</div>",
        guide_scheme_card(
            "scheme-card--main",
            kicker="Основа",
            title="Обзор данных",
            author=AUTHORS.get(main_href, ""),
            note="Ознакомление, отчистка, распределения, цели и планы веток",
        ),
        '<div class="tree-v2-side tree-v2-side--right">',
        '<span class="tree-v2-hbar tree-v2-hbar--thin tree-v2-hbar--dash" aria-hidden="true"></span>',
        guide_scheme_card(
            "scheme-card--side",
            kicker="Дополнение",
            title="Описание признаков",
            author=AUTHORS.get("features.html", ""),
            note="Доп. информация по исследуемым признакам",
        ),
        "</div>",
        "</div>",
        GUIDE_TRUNK_VBAR,
    ]
    for sprint_name, sprint_notebooks in [
        (SPRINTS[0][0], s1_notebooks),
        (SPRINTS[1][0], s2_notebooks),
    ]:
        layout = GUIDE_SPRINT_LAYOUT[sprint_name]
        parts.append(guide_sprint_block(sprint_name, sprint_notebooks, layout))
        parts.append(GUIDE_TRUNK_VBAR)
    if parts[-1] == GUIDE_TRUNK_VBAR:
        parts.pop()
    for href, title in extra_main:
        parts.append(GUIDE_TRUNK_VBAR)
        parts.append('<div class="tree-v2-trunk-node">')
        parts.append(
            guide_scheme_card(
                "scheme-card--main",
                kicker="Доп. ветка",
                title="Визуализация генератора",
                author=AUTHORS.get(href, ""),
            )
        )
        parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts)


def guide_html():
    return GUIDE_INTRO + guide_tree_html() + GUIDE_ROUTE + GUIDE_FEATURE_HINT


KICKER = "Лабораторная работа 01"
TITLE = "Инфохимия. Статистический анализ свойств молекул"
INTRO = """
<p><strong>Этот репозиторий и сайт</strong> Материалы лабораторной по инфохимии: статистический анализ свойств молекул на реальных данных. Здесь собраны очищенный датасет, ноутбуки с расчётами, выводами и графиками, а также страницы для чтения без запуска кода. Задача работы — рассмотреть числовые характеристики веществ как случайные величины: оценить распределения, связи, выборки и гипотезы, а затем перейти к моделированию.</p>
<p><strong>Исходные данные</strong> Выборка из базы DrugBank: лекарственные соединения и заранее посчитанные для них дескрипторы (молекулярные признаки). После очистки от экспериментальных признаков и служебных полей остаются тысячи строк; каждая строка — одна молекула, каждый столбец — одна числовая (или категориальная) характеристика, пригодная для статистики. Именно с этим набором команда выполняет последующую работу.</p>
<p><strong>Спринт 1 — анализ</strong> Сначала идёт обзор всего датасета: пропуски, распределения, корреляции, план дальнейших разборов. Затем в отдельных ноутбуках команда разбирает выбранные пары признаков по единому плану: обосновывает стохастику (случайность), проверяет зависимости, выполняет анализ и формулирует итоги.</p>
<p><strong>Спринт 2 — генератор</strong> Команда реализует генераторы случайных величин по эмпирическим или теоретическим распределениям данных первого спринта: у каждого свой метод, общий интерфейс (BaseGenerator, инициализация по данным), сравнение с исходным распределением на графиках и по статистикам, статистические тесты и выводы о качестве.</p>
<p>Главная страница расчётов не содержит: она объясняет устройство работы и порядок чтения. В ноутбуках код свёрнут под пунктом «Код», графики под пунктом «Графики». Слева — меню по всей работе, справа — оглавление открытой страницы.</p>
"""

CHEMIST = (
    "Исследует свойства молекул и разрабатывает свою часть статистического анализа: "
    "смотрит, как устроены величины, как они связаны, и проверяет гипотезы."
)

TEAM = """
<table class="team">
<thead><tr><th>Инфохимики</th><th>Дизайнер</th></tr></thead>
<tbody>
<tr>
<td>
<p class="who">Сычев Александр<span class="isu">467653</span><span class="roles">тимлид | разработчик | исследователь</span></p>
<p class="files">Обзор данных, Описание признаков</p>
<p class="role">Руководил командой: составил план выполнения работы, подобрал начальные данные, с которыми шла дальнейшая работа, и отдал остальным сокомандникам индивидуальные задания. {chemist}</p>
</td>
<td rowspan="4">
<p class="who">Закликовский Иван<span class="isu">503803</span><span class="roles">дизайнер | разработчик | исследователь</span></p>
<p class="files">Растворимость и молекулярная масса</p>
<p class="role">Собрал и оформил этот сайт, оформил ноутбуки команды и переформулировал тексты. {chemist}</p>
</td>
</tr>
<tr>
<td>
<p class="who">Петрунина Анна<span class="isu">327017</span><span class="roles">разработчик | исследователь</span></p>
<p class="files">Акцепторы и доноры</p>
<p class="role">{chemist}</p>
</td>
</tr>
<tr>
<td>
<p class="who">Родичева Варвара<span class="isu">502343</span><span class="roles">разработчик | исследователь</span></p>
<p class="files">&lt;пока нет&gt;</p>
<p class="role">{chemist}</p>
</td>
</tr>
<tr>
<td>
<p class="who">Авсиевич Евдокия<span class="isu">464929</span><span class="roles">разработчик | исследователь</span></p>
<p class="files">&lt;пока нет&gt;</p>
<p class="role">{chemist}</p>
</td>
</tr>
</tbody>
</table>
""".format(chemist=CHEMIST)

CAT_MARK_TABLE = """
<h3 class="cat-mark-title">Таблица</h3>
<table class="cat-mark-table">
<thead>
<tr><th>cat_id</th><th>notebook_link</th><th>coeff</th><th>comment</th></tr>
</thead>
<tbody>
<tr>
<td>lab.ic.01 Сычев Александр 467653</td>
<td><a href="data_review.html">Обзор данных</a><br><a href="features.html">Описание признаков</a></td>
<td>—</td><td>?</td>
</tr>
<tr>
<td>lab.ic.01 Петрунина Анна 327017</td>
<td><a href="hbond_simple.html">Акцепторы и доноры</a></td>
<td>—</td><td>?</td>
</tr>
<tr>
<td>lab.ic.01 Родичева Варвара 502343</td>
<td>—</td>
<td>—</td><td>?</td>
</tr>
<tr>
<td>lab.ic.01 Авсиевич Евдокия 464929</td>
<td>—</td>
<td>—</td><td>?</td>
</tr>
<tr>
<td>lab.de.01 Закликовский Иван 503803</td>
<td><a href="logs_mw_ktvd.html">Растворимость и молекулярная масса</a><br><a href="generator_viz.html">Визуализация генератора</a></td>
<td>—</td><td>?</td>
</tr>
</tbody>
</table>
"""

PAGE_STYLE = """
<style>
:root {
    color-scheme: light;
    --bg: #f6f6f6;
    --surface: #fff;
    --surface-2: #fafafa;
    --text: #222;
    --muted: #666;
    --muted-2: #777;
    --line: #ddd;
    --line-soft: #eee;
    --line-faint: #e4e4e4;
    --hover: #eee;
    --current: #ddd;
    --table-head: #f3f3f3;
    --scheme-line: #146c34;
    --scheme-dash: #146c34;
    --heading: #146c34;
    --accent-bg: #e7f5ec;
}
html[data-theme="dark"] {
    color-scheme: dark;
    --bg: #171717;
    --surface: #242424;
    --surface-2: #2e2e2e;
    --text: #eee;
    --muted: #aaa;
    --muted-2: #999;
    --line: #3f3f3f;
    --line-soft: #333;
    --line-faint: #3a3a3a;
    --hover: #353535;
    --current: #454545;
    --table-head: #303030;
    --scheme-line: #5ca67c;
    --scheme-dash: #5ca67c;
    --heading: #5ca67c;
    --accent-bg: #243028;
    --jp-layout-color0: #242424;
    --jp-layout-color1: #242424;
    --jp-layout-color2: #2e2e2e;
    --jp-layout-color3: #3f3f3f;
    --jp-ui-font-color0: rgba(255, 255, 255, 0.9);
    --jp-ui-font-color1: rgba(255, 255, 255, 0.87);
    --jp-ui-font-color2: rgba(255, 255, 255, 0.7);
    --jp-ui-font-color3: rgba(255, 255, 255, 0.5);
    --jp-content-font-color0: rgba(255, 255, 255, 0.9);
    --jp-content-font-color1: rgba(255, 255, 255, 0.87);
    --jp-content-font-color2: rgba(255, 255, 255, 0.7);
    --jp-content-font-color3: rgba(255, 255, 255, 0.5);
    --jp-content-link-color: #9ec1ff;
    --jp-border-color0: #3f3f3f;
    --jp-border-color1: #4a4a4a;
    --jp-border-color2: #555;
    --jp-rendermime-table-row-background: transparent;
    --jp-rendermime-table-row-hover-background: #303030;
    --jp-cell-editor-background: #2e2e2e;
    --jp-mirror-editor-variable-color: #e6e6e6;
    --jp-mirror-editor-keyword-color: #7dcea0;
    --jp-mirror-editor-builtin-color: #7dcea0;
    --jp-mirror-editor-operator-color: #c4b6e0;
    --jp-mirror-editor-punctuation-color: #c8c8c8;
    --jp-mirror-editor-number-color: #e0c36a;
    --jp-mirror-editor-string-color: #e0a070;
    --jp-mirror-editor-string-2-color: #e0a070;
    --jp-mirror-editor-comment-color: #8d8d8d;
    --jp-mirror-editor-def-color: #8ec8e8;
    --jp-mirror-editor-variable-2-color: #8ec8e8;
    --jp-mirror-editor-variable-3-color: #7dcea0;
    --jp-mirror-editor-property-color: #8ec8e8;
    --jp-mirror-editor-atom-color: #8ec8e8;
    --jp-mirror-editor-meta-color: #c4b6e0;
    --jp-mirror-editor-qualifier-color: #b0b0b0;
    --jp-mirror-editor-bracket-color: #b0b0b0;
    --jp-mirror-editor-tag-color: #7dcea0;
    --jp-mirror-editor-attribute-color: #e0c36a;
    --jp-mirror-editor-error-color: #e07070;
}
body { margin: 0; font-family: sans-serif; color: var(--text); background: var(--bg); }
.topbar { padding: 1.6rem 1.8rem; background: var(--surface); border-bottom: 1px solid var(--line); }
.kicker { margin: 0; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); }
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
.sidebar a:hover { color: var(--text); text-decoration: none; }
.sidebar summary { display: block; list-style: none; cursor: pointer; }
.sidebar summary::-webkit-details-marker { display: none; }
.sidebar summary::marker { content: ""; }
.sidebar-box {
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    max-height: calc(100vh - 8rem);
    overflow: auto;
    overscroll-behavior: contain;
    padding: 0.7rem;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
}
.sidebar-box > a,
.sidebar-box > details {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 6px;
    transition: border-color 0.15s ease, background 0.15s ease;
}
.sidebar-box > a,
.sidebar-box > details > summary {
    display: block;
    padding: 0.8rem 1rem;
    border-radius: 6px;
    transition: color 0.15s ease, background 0.15s ease;
}
.sidebar-nav-section .sidebar-nav-panel {
    overflow: hidden;
    max-height: 0;
    opacity: 0;
    transition: max-height 0.48s ease, opacity 0.4s ease;
}
.sidebar-nav-section.is-open:not(.is-retracting) .sidebar-nav-panel {
    max-height: 32rem;
    opacity: 1;
}
.sidebar-nav-section.is-retracting .sidebar-nav-panel {
    max-height: 0;
    opacity: 0;
}
.sidebar details details { margin: 0.65rem 0.6rem; background: var(--surface-2); border: 1px solid var(--line-faint); border-radius: 6px; }
.sidebar details details > summary { display: block; padding: 0; border-radius: 6px; }
.sidebar details details > summary a { display: block; padding: 0.6rem 0.75rem; border-radius: 6px; }
.sidebar details details > summary a:hover { background: var(--hover); }
.notebook-item { position: relative; margin: 0.65rem 0.6rem; }
.notebook-link {
    display: block;
    margin: 0.65rem 0.6rem;
    padding: 0.6rem 0.75rem;
    border: 1px solid var(--line-faint);
    border-radius: 6px;
    background: var(--surface-2);
    color: var(--text);
}
.notebook-link:hover { background: var(--hover); }
.toc-pop .open-notebook { display: block; padding: 0.35rem 0.6rem; }
.sidebar .toc { margin: 0.2rem 0 0.4rem 1rem; padding: 0; list-style: none; }
.sidebar .empty { margin: 0.2rem 0.6rem 0.6rem; color: var(--muted-2); font-size: 0.9rem; }
.sidebar.page-toc {
    left: auto;
    right: 1rem;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0.55rem;
}
.page-toc .sidebar-box.page-toc-box {
    flex: 1 1 auto;
    min-height: 0;
    gap: 0.55rem;
    padding: 0.45rem;
    overscroll-behavior: contain;
}
.page-toc .sidebar-box.feature-lookup-box {
    flex: 0 0 auto;
    padding: 0;
    border: none;
    background: transparent;
    overflow: visible;
}
.page-toc-scroll {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
}
.page-toc .page-toc-scroll > a {
    display: block;
    padding: 0.45rem 0.7rem;
    border-radius: 6px;
    font-size: 0.92rem;
    line-height: 1.3;
    border: 1px solid var(--line-faint);
    background: var(--surface-2);
}
.page-toc .page-toc-scroll > a:hover { background: var(--hover); }
.page-toc .page-toc-scroll > a.is-current,
.page-toc .page-toc-scroll > a.is-current:hover {
    border-color: var(--heading);
    color: var(--heading);
    background: var(--accent-bg);
}
.feature-lookup-field {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    width: 100%;
    border: 1px solid var(--line-faint);
    border-radius: 6px;
    background: var(--surface-2);
    overflow: hidden;
    transition: border-color 0.15s ease, background 0.15s ease;
}
.feature-lookup-field.is-match {
    border-color: var(--heading);
}
.feature-lookup-field.is-invalid { border-color: #c55; }
.feature-lookup-search {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0 0.55rem 0 0.65rem;
    min-height: 2.35rem;
    transition: color 0.15s ease, background 0.15s ease;
}
.feature-lookup-field.is-match .feature-lookup-search {
    color: var(--heading);
    background: var(--accent-bg);
}
.feature-lookup-icon {
    flex: 0 0 auto;
    display: flex;
    width: 1.05rem;
    height: 1.05rem;
    color: var(--muted-2);
}
.feature-lookup-field.is-match .feature-lookup-icon { color: var(--heading); }
.feature-lookup-icon svg { display: block; width: 100%; height: 100%; }
.feature-lookup-input {
    display: block;
    flex: 1 1 auto;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
    padding: 0.45rem 0.65rem 0.45rem 0;
    border: 0;
    border-radius: 0;
    font: inherit;
    font-size: 0.92rem;
    line-height: 1.3;
    color: var(--text);
    background: transparent;
    transition: color 0.15s ease;
}
.feature-lookup-field.is-match .feature-lookup-input { color: var(--heading); }
.feature-lookup-input:focus { outline: none; }
.feature-lookup-input::placeholder { color: var(--muted-2); }
.feature-lookup-result {
    padding: 0.5rem 0.7rem 0.65rem;
    border-top: 1px solid var(--line-soft);
    font-size: 0.84rem;
    line-height: 1.4;
}
.feature-lookup-desc { margin: 0 0 0.35rem; color: var(--text); }
.feature-lookup-kind { margin: 0; color: var(--muted-2); font-size: 0.8rem; }
.feature-lookup-miss { margin: 0; color: var(--muted-2); }
.prose p { margin: 0 0 0.85rem; font-size: 1.05rem; line-height: 1.6; }
.prose p:last-child { margin-bottom: 0; }
.prose-intro { font-size: 1.02rem; line-height: 1.72; }
.prose-intro p { margin: 0 0 1.45rem; }
.prose-intro p:last-child {
    margin-top: 0.5rem;
    padding-top: 1.1rem;
    border-top: 1px solid var(--line-soft);
    font-size: 0.94rem;
    line-height: 1.62;
    color: var(--muted);
}
.prose-intro p > strong {
    display: block;
    margin-bottom: 0.45rem;
    font-size: 1.14rem;
    font-weight: 600;
    line-height: 1.35;
    color: var(--heading);
    letter-spacing: 0.01em;
}
.prose-intro p:first-child > strong { font-size: 1.18rem; }
.prose-intro p:first-child {
    font-size: 1.06rem;
    line-height: 1.75;
}
.panel#vvedenie h2 {
    margin-bottom: 1.15rem;
    padding-bottom: 0.9rem;
    border-bottom: 1px solid var(--line-soft);
}
.scheme-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.28rem;
    width: 100%;
    max-width: 17.5rem;
    padding: 0.85rem 0.95rem;
    background: var(--surface-2);
    border: 1px solid var(--line);
    border-radius: 6px;
    box-sizing: border-box;
}
.scheme-card strong { font-size: 1rem; line-height: 1.3; font-weight: 600; }
.scheme-kicker { color: var(--muted); font-size: 0.86rem; }
.scheme-author { color: var(--muted-2); font-size: 0.78rem; line-height: 1.3; }
.scheme-note { color: var(--muted); font-size: 0.84rem; line-height: 1.35; }
.tree-v2 {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 2.2rem 0 2.4rem;
    --tree-thick: 9px;
    --tree-arm: 2.35rem;
    --tree-arm-wide: 1.88rem;
    --tree-card: 16.75rem;
    --tree-card-leaf: 13.96rem;
}
.tree-v2 .scheme-card--leaf {
    width: var(--tree-card-leaf);
    max-width: var(--tree-card-leaf);
    padding: 0.72rem 0.8rem;
    box-sizing: border-box;
}
.tree-v2 .scheme-card--leaf strong { font-size: 0.92rem; }
.tree-v2 .scheme-card--leaf .scheme-author { font-size: 0.72rem; }
.tree-v2-root { --tree-arm: 3.65rem; }
.tree-v2-root .scheme-card {
    width: var(--tree-card);
    max-width: var(--tree-card);
    box-sizing: border-box;
}
.tree-v2-root {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    align-items: center;
    gap: 0;
    column-gap: 0.25rem;
    width: min(100%, 52rem);
}
.tree-v2-sprint-mid .scheme-card--sprint-wide {
    width: var(--tree-card);
    max-width: var(--tree-card);
    min-width: var(--tree-card);
    min-height: 9.75rem;
    padding: 0.95rem 0.95rem 1.05rem;
    justify-content: flex-start;
    align-items: flex-start;
    box-sizing: border-box;
}
.tree-v2-sprint-mid .scheme-card--sprint-wide .scheme-note { line-height: 1.35; }
.scheme-sprint-extra {
    width: 100%;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--line-soft);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.28rem;
}
.scheme-sprint-extra strong { font-size: 0.96rem; }
.tree-v2-side { display: flex; align-items: center; gap: 0; min-width: 0; }
.tree-v2-side--left { justify-content: flex-end; }
.tree-v2-side--right { justify-content: flex-start; }
.tree-v2-hbar--thin {
    display: block;
    width: var(--tree-arm);
    height: 0;
    flex: 0 0 var(--tree-arm);
    border-top: 1px solid var(--scheme-line);
    background: none;
}
.tree-v2-hbar--thick {
    display: block;
    width: var(--tree-arm);
    height: var(--tree-thick);
    flex: 0 0 var(--tree-arm);
    background: var(--heading);
    border-radius: 2px;
    align-self: center;
}
.tree-v2-hbar--dash { border-top-style: dashed; border-top-color: var(--scheme-dash); }
.tree-v2-hbar--muted { border-top-color: var(--line); }
.tree-v2-vbar--thin {
    display: block;
    width: 0;
    height: 1.6rem;
    margin: 0.2rem auto;
    border-left: 1px solid var(--scheme-line);
}
.tree-v2-vbar--trunk {
    height: 8rem;
    margin: 0 auto;
    flex-shrink: 0;
}
.tree-v2-trunk-node {
    display: flex;
    justify-content: center;
    width: min(100%, 58rem);
}
.tree-v2-trunk-node .scheme-card {
    width: var(--tree-card);
    max-width: var(--tree-card);
}
.tree-v2-sprint {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: min(100%, 58rem);
}
.tree-v2-sprint-row {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: center;
    gap: 0;
    width: 100%;
    --tree-arm: var(--tree-arm-wide);
}
.tree-v2-sprint-row--wide { width: min(100%, 58rem); }
.tree-v2-sprint-mid {
    display: flex;
    justify-content: center;
    align-items: stretch;
    flex: 0 0 auto;
    align-self: stretch;
}
.tree-v2-sprint-mid .scheme-card--sprint-wide {
    flex: 1 1 auto;
    align-self: stretch;
    height: 100%;
}
.tree-v2-leaves {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    padding: 0.35rem 0;
    flex: 0 0 auto;
    align-self: center;
}
.scheme-card--leaf-tbd {
    border-color: var(--line-faint);
    border-style: dashed;
    opacity: 0.7;
}
.scheme-card--leaf-tbd strong { color: var(--muted-2); font-weight: 500; }
.tree-v2-leaves--left { align-items: flex-end; padding-right: 0; }
.tree-v2-leaves--right { align-items: flex-start; padding-left: 0; }
.tree-v2-leaf-row { display: flex; align-items: center; gap: 0; }
.scheme-card--main,
.scheme-card--sprint,
.scheme-card--leaf { border-color: var(--heading); }
.scheme-card--side {
    border-color: var(--muted);
    background: var(--surface);
    color: var(--muted-2);
}
.scheme-card--side strong { color: var(--text); font-weight: 500; }
.scheme-card--ghost.scheme-card--minor {
    border-color: var(--line-faint);
    background: transparent;
    color: var(--muted-2);
    opacity: 0.92;
}
.scheme-card--ghost.scheme-card--minor strong {
    color: var(--muted-2);
    font-weight: 500;
    font-size: 0.88rem;
}
.tree-v2-root .scheme-card--sources-compact {
    width: auto;
    max-width: none;
    min-width: 0;
    padding: 0.5rem 0.7rem;
    gap: 0;
}
.tree-v2-root .scheme-card--sources-compact strong {
    font-size: 0.92rem;
}
.route { list-style: none; margin: 0; padding: 0; counter-reset: stop; }
.route > li { display: grid; grid-template-columns: 2.3rem 1fr; gap: 0.75rem; padding: 0.95rem 0; border-top: 1px solid var(--line-soft); }
.route > li::before { counter-increment: stop; content: counter(stop); width: 2.3rem; height: 2.3rem; display: flex; align-items: center; justify-content: center; border: 1px solid var(--line); border-radius: 6px; background: var(--surface-2); font-weight: 600; }
.route h3 { margin: 0.15rem 0 0.35rem; font-size: 1.05rem; }
.route p { margin: 0; line-height: 1.55; }
.route p.route-sub { margin-top: 0.55rem; color: var(--muted); font-size: 0.98rem; }
.route-feature-hint {
    margin-top: 1.25rem;
    padding: 0.9rem 1.05rem;
    background: var(--accent-bg);
    border: 1px solid var(--scheme-line);
    border-radius: 8px;
    font-size: 0.96rem;
    line-height: 1.55;
}
.route-feature-hint p { margin: 0; }
.route-feature-hint code {
    font-size: 0.9em;
    padding: 0.1em 0.35em;
    border-radius: 4px;
    background: var(--surface-2);
}
.code { font-family: monospace; font-size: 0.92em; }
.content { margin-left: 22rem; margin-right: 22rem; min-width: 0; padding: 1.5rem 1rem 3rem 1rem; }
.panel { width: 100%; padding: 1.3rem 1.5rem; background: var(--surface); border: 1px solid var(--line); border-radius: 6px; box-sizing: border-box; }
.panel + .panel { margin-top: 1rem; }
.panel h2 { margin: 0 0 0.8rem; font-size: 1.35rem; }
.panel table.team { margin-top: 0; }
.panel table.team td:first-child { font-family: sans-serif; white-space: normal; }
.team .who { margin: 0; font-weight: 600; }
.team .isu { margin-left: 0.4rem; color: var(--muted-2); font-weight: 400; font-size: 0.86rem; }
.team .roles { margin-left: 0.55rem; font-weight: 400; }
h1, h2, h3, h4, h5, h6,
.jp-RenderedHTMLCommon h1,
.jp-RenderedHTMLCommon h2,
.jp-RenderedHTMLCommon h3,
.jp-RenderedHTMLCommon h4,
.jp-RenderedHTMLCommon h5,
.jp-RenderedHTMLCommon h6 { color: var(--heading); }
body.jp-Notebook .jp-RenderedHTMLCommon h1 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    padding-bottom: 0;
    border-bottom: none;
}
body.jp-Notebook .jp-RenderedHTMLCommon h2,
body.jp-Notebook .jp-RenderedHTMLCommon h3,
body.jp-Notebook .jp-RenderedHTMLCommon h4 {
    padding-bottom: 0.55rem;
    margin-top: 1.35rem;
    margin-bottom: 0.85rem;
    border-bottom: 1px solid var(--line-soft);
}
body.jp-Notebook .jp-RenderedHTMLCommon h2:first-child,
body.jp-Notebook .jp-RenderedHTMLCommon h3:first-child,
body.jp-Notebook .jp-RenderedHTMLCommon h4:first-child {
    margin-top: 0;
}
body.jp-Notebook .research-outline {
    margin-top: 0.35rem;
}
body.jp-Notebook .research-outline p:has(> strong:only-child) {
    margin: 1.35rem 0 0.45rem;
    padding-top: 0.95rem;
    border-top: 1px solid var(--line-soft);
}
body.jp-Notebook .research-outline > p:first-child:has(> strong:only-child) {
    margin-top: 0.65rem;
    padding-top: 0;
    border-top: none;
}
body.jp-Notebook .research-outline p:has(> strong:only-child) > strong {
    font-weight: 700;
    font-size: 1.03rem;
    line-height: 1.45;
    color: var(--text);
}
html[data-theme="dark"] body.jp-Notebook .research-outline p:has(> strong:only-child) > strong,
html[data-theme="dark"] body.jp-Notebook .research-outline li > p > strong {
    color: #f3f4f2;
}
body.jp-Notebook .research-outline li {
    margin: 0.85rem 0;
    padding-left: 0.15rem;
}
body.jp-Notebook .research-outline li > p {
    margin: 0;
    line-height: 1.62;
}
body.jp-Notebook .research-outline li > p > strong {
    font-weight: 700;
    color: var(--text);
}
body.jp-Notebook .research-outline h3 {
    margin-top: 2rem;
    padding-bottom: 0.55rem;
    margin-bottom: 0.65rem;
    border-bottom: 1px solid var(--line-soft);
}
body.jp-Notebook .research-outline h3:first-of-type {
    margin-top: 1.5rem;
}
body.jp-Notebook .research-outline h3 + p:has(> strong:only-child) {
    border-top: none;
    padding-top: 0;
    margin-top: 0.55rem;
}
body.jp-Notebook .meme-row {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.85rem;
    margin: 0.9rem 0 1.15rem;
    align-items: flex-start;
    justify-content: center;
}
body.jp-Notebook .meme-row img {
    flex: 0 1 auto;
    max-width: calc((50% - 0.45rem) / 1.5);
    max-height: 11.5rem;
    width: auto;
    height: auto;
    object-fit: contain;
    border-radius: 6px;
    border: 1px solid var(--line-soft);
}
body.jp-Notebook .notebook-takeaway {
    margin: 1.05rem 0 1.35rem;
    padding: 0.9rem 1.05rem 1rem;
    background: var(--accent-bg);
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    line-height: 1.62;
}
body.jp-Notebook .notebook-takeaway > :first-child {
    margin-top: 0;
}
body.jp-Notebook .notebook-takeaway > :last-child {
    margin-bottom: 0;
}
body.jp-Notebook .notebook-takeaway p > strong:first-child {
    font-weight: 700;
    color: var(--text);
}
body.jp-Notebook .notebook-takeaway p:has(> strong:only-child) {
    margin: 1.1rem 0 0.4rem;
    padding-top: 0.8rem;
    border-top: 1px solid var(--line-soft);
}
body.jp-Notebook .notebook-takeaway > p:first-child:has(> strong:only-child),
body.jp-Notebook .notebook-takeaway > p:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
}
body.jp-Notebook .notebook-takeaway ul {
    margin: 0.5rem 0 0.25rem;
    padding-left: 1.25rem;
}
body.jp-Notebook .notebook-takeaway ul li > p > strong {
    font-weight: 700;
    color: var(--text);
}
html[data-theme="dark"] body.jp-Notebook .notebook-takeaway p > strong,
html[data-theme="dark"] body.jp-Notebook .notebook-takeaway li > p > strong,
html[data-theme="dark"] body.jp-Notebook .notebook-takeaway p:has(> strong:only-child) > strong {
    color: #f3f4f2;
}
body.jp-Notebook .research-outline ol {
    margin: 0.35rem 0 0;
    padding-left: 1.35rem;
    list-style-position: outside;
}
body.jp-Notebook .resume-outline {
    margin-top: 0.25rem;
}
body.jp-Notebook .resume-outline ol {
    margin: 0;
    padding-left: 1.35rem;
    list-style-position: outside;
}
body.jp-Notebook .resume-outline ol > li {
    margin: 0;
    padding: 0.75rem 0 0.75rem 0.15rem;
    border: none;
}
body.jp-Notebook .resume-outline ol > li + li {
    border-top: 1px solid var(--line-soft);
}
body.jp-Notebook .resume-outline ol > li:first-child {
    padding-top: 0.35rem;
}
body.jp-Notebook .resume-outline ol > li:last-child {
    padding-bottom: 0;
}
body.jp-Notebook .resume-outline ol > li > p {
    font-size: 1.03rem;
    line-height: 1.62;
    margin: 0;
}
body.jp-Notebook .resume-outline ol > li > p > strong {
    font-weight: 700;
    font-size: 1.03rem;
    color: var(--text);
}
html[data-theme="dark"] body.jp-Notebook .resume-outline ol > li > p > strong {
    color: #f3f4f2;
}
.route > li::before { color: var(--heading); border-color: var(--heading); }
.team th,
.team .roles { color: var(--heading); }
.sidebar:not(.page-toc) .sidebar-box > a:hover,
.sidebar:not(.page-toc) .sidebar-box > a.is-current,
.sidebar:not(.page-toc) .sidebar-box > a.is-current:hover {
    color: var(--heading);
    border-color: var(--heading);
    background: var(--accent-bg);
}
.sidebar:not(.page-toc) .sidebar-box > details:has(> summary:hover) {
    border-color: var(--heading);
    background: var(--accent-bg);
}
.sidebar:not(.page-toc) .sidebar-box > details > summary:hover {
    color: var(--heading);
    background: var(--accent-bg);
}
.sidebar:not(.page-toc) .notebook-link:hover,
.sidebar:not(.page-toc) details details > summary a:hover {
    color: var(--heading);
    border-color: var(--heading);
    background: var(--accent-bg);
}
.page-toc .page-toc-scroll > a.is-current,
.page-toc .page-toc-scroll > a.is-current:hover,
.sidebar:not(.page-toc) .notebook-link.is-current,
.sidebar:not(.page-toc) .notebook-link.is-current:hover {
    color: var(--heading);
    border-color: var(--heading);
    background: var(--accent-bg);
}
.sidebar:not(.page-toc) details details:has(a.is-current) {
    border-color: var(--heading);
    background: var(--accent-bg);
}
.sidebar:not(.page-toc) details details:has(a.is-current) > summary a {
    color: var(--heading);
    background: transparent;
}
.team .files { margin: 0.35rem 0 0; color: var(--muted-2); font-size: 0.86rem; }
.team .role { margin: 0.55rem 0 0; line-height: 1.5; }
.cat-mark-title {
    margin: 1.75rem 0 0.65rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--heading);
}
.cat-mark-table { margin-top: 0; }
.panel table { width: 100%; border-collapse: collapse; margin-top: 0.4rem; }
.panel th, .panel td { padding: 0.55rem 0.7rem; border: 1px solid var(--line); text-align: left; vertical-align: top; }
.panel th { background: var(--table-head); }
.panel td:first-child { font-family: monospace; white-space: nowrap; }
.code-fold {
    margin: 0.4rem 0 0.8rem;
    width: fit-content;
    max-width: 100%;
    background: var(--surface-2);
    border: 1px solid var(--line);
    border-radius: 6px;
    overflow: hidden;
}
html[data-theme="dark"] .code-fold { border-color: #e6e6e6; }
.code-fold[open] { width: 100%; }
.code-fold > summary {
    display: list-item;
    cursor: pointer;
    padding: 0.4rem 0.75rem;
    color: var(--text);
    background: transparent;
}
.code-fold[open] > summary { border-bottom: 1px solid var(--line); }
html[data-theme="dark"] .code-fold[open] > summary { border-bottom-color: #e6e6e6; }
body.jp-Notebook .code-fold .jp-InputArea-editor,
body.jp-Notebook .code-fold .highlight {
    border: none;
    box-shadow: none;
}
.table-sheet {
    margin: 0.6rem 0 0.9rem;
    padding: 0.65rem 0.7rem;
    background: var(--surface-2);
    border: 1px solid var(--line);
    border-radius: 6px;
    overflow-x: auto;
}
body.jp-Notebook .table-sheet table.dataframe {
    width: max-content;
    border-collapse: collapse;
    margin: 0;
    font-size: 0.86rem;
}
body.jp-Notebook .table-sheet table.dataframe th,
body.jp-Notebook .table-sheet table.dataframe td {
    border: 1px solid var(--line);
    padding: 0.4rem 0.55rem;
    text-align: left;
    vertical-align: middle;
    color: var(--text);
    background: transparent;
    white-space: nowrap;
}
body.jp-Notebook .table-sheet table.dataframe thead th { background: var(--table-head); }
.table-sheet-center {
    display: flex;
    justify-content: center;
    width: 100%;
    box-sizing: border-box;
}
.table-sheet-center table {
    width: max-content;
    max-width: 100%;
    margin: 0;
    border-collapse: collapse;
    table-layout: auto;
}
.table-sheet-center th,
.table-sheet-center td {
    border: 1px solid var(--line);
    padding: 0.45rem 0.7rem;
    color: var(--text);
}
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
    color: var(--text);
    text-decoration: none;
}
.sidebar .byline {
    display: block;
    margin-top: 0.18rem;
    color: var(--muted-2);
    font-size: 0.78rem;
    font-weight: 400;
    line-height: 1.3;
}
.sidebar:not(.page-toc) .byline-reveal .byline {
    margin-top: 0;
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: opacity 0.15s ease, max-height 0.15s ease, margin-top 0.15s ease;
}
.sidebar:not(.page-toc) .byline-reveal:hover .byline,
.sidebar:not(.page-toc) .byline-reveal.is-current .byline {
    max-height: 2.5rem;
    opacity: 1;
    margin-top: 0.18rem;
}
body.jp-Notebook { background: var(--bg); color: var(--text); }
body.jp-Notebook main {
    display: block;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 1.3rem 1.5rem 1.8rem;
    box-sizing: border-box;
}
body.jp-Notebook .jp-Cell,
body.jp-Notebook .jp-Cell-inputWrapper,
body.jp-Notebook .jp-InputArea,
body.jp-Notebook .jp-RenderedHTMLCommon,
body.jp-Notebook .jp-OutputArea,
body.jp-Notebook .jp-OutputArea-output {
    background: transparent;
    border: none;
    box-shadow: none;
}
body.jp-Notebook .jp-Collapser { display: none; }
html[data-theme="dark"] body.jp-Notebook .jp-InputArea-editor,
html[data-theme="dark"] body.jp-Notebook .cm-editor,
html[data-theme="dark"] body.jp-Notebook .highlight,
html[data-theme="dark"] body.jp-Notebook .highlight pre {
    background: var(--surface-2);
    color: var(--text);
}
body.jp-Notebook .jp-Cell-inputWrapper { padding: 0; }
body.jp-Notebook .jp-MarkdownCell .jp-Cell-inputWrapper {
    display: block;
    width: 100%;
}
body.jp-Notebook .jp-MarkdownCell .jp-InputArea,
body.jp-Notebook .jp-MarkdownCell .jp-RenderedMarkdown {
    display: block;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}
body.jp-Notebook .jp-MarkdownCell .table-sheet {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}
body.jp-Notebook .jp-OutputArea-output.jp-RenderedText {
    display: block;
    width: 100%;
    max-width: 100%;
    margin: 0.7rem 0 0.95rem;
    padding: 0.78rem 0.95rem;
    background: var(--surface-2);
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    box-sizing: border-box;
}
body.jp-Notebook .jp-OutputArea-output.jp-RenderedText pre {
    margin: 0;
    padding: 0;
    background: transparent;
    border: none;
    box-shadow: none;
    font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
    font-size: 0.92rem;
    line-height: 1.52;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
}
body.jp-Notebook .jp-OutputArea-output.jp-RenderedText[data-mime-type="application/vnd.jupyter.stderr"] {
    border-color: var(--line);
    background: var(--accent-bg);
}
.theme-toggle {
    position: fixed;
    right: 1rem;
    bottom: 1rem;
    z-index: 30;
    width: 3.5rem;
    height: 3.5rem;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    color: var(--text);
    cursor: pointer;
}
.theme-toggle svg { width: 1.6rem; height: 1.6rem; display: block; }
html[data-theme="dark"] .dataframe,
html[data-theme="dark"] .dataframe th,
html[data-theme="dark"] .dataframe td {
    color: var(--text);
    background: transparent;
    border-color: var(--line);
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
    var pageName = (location.pathname.split("/").pop() || "index.html").split("?")[0];
    aside.querySelectorAll("a").forEach(function (link) {
        var href = (link.getAttribute("href") || "").split("#")[0].split("?")[0];
        if (href.split("/").pop() === pageName) link.classList.add("is-current");
    });
    var navBox = aside.querySelector(".sidebar-box");
    var NAV_CLOSE_MS = 520;
    if (navBox) {
        Array.prototype.forEach.call(navBox.children, function (node) {
            if (node.tagName !== "DETAILS" || !node.classList.contains("sidebar-nav-section")) {
                return;
            }
            function sectionHasCurrent() {
                return !!node.querySelector(".is-current");
            }
            node.open = true;
            if (sectionHasCurrent()) node.classList.add("is-open");
            var summary = node.querySelector("summary");
            if (!summary) return;
            summary.addEventListener("click", function (e) {
                e.preventDefault();
                if (node.classList.contains("is-open")) {
                    node.classList.add("is-retracting");
                    clearTimeout(node._navCloseTimer);
                    node._navCloseTimer = setTimeout(function () {
                        node.classList.remove("is-open", "is-retracting");
                    }, NAV_CLOSE_MS);
                    return;
                }
                node.classList.remove("is-retracting");
                node.classList.add("is-open");
            });
        });
    }
    content.className = "content";
    while (document.body.firstChild) {
        content.appendChild(document.body.firstChild);
    }
    layout.appendChild(aside);
    layout.appendChild(content);
    document.body.appendChild(bar);
    document.body.appendChild(layout);

    function foldBlock(node, label) {
        var details = document.createElement("details");
        var summary = document.createElement("summary");
        details.className = "code-fold";
        summary.textContent = label;
        node.parentNode.insertBefore(details, node);
        details.appendChild(summary);
        details.appendChild(node);
    }
    document.querySelectorAll(".jp-CodeCell .jp-InputArea, .code_cell .input_area").forEach(function (area) {
        foldBlock(area, "Код");
    });
    document.querySelectorAll(".jp-RenderedImage").forEach(function (image) {
        foldBlock(image, "График");
    });
    document.querySelectorAll(".jp-RenderedHTML table.dataframe").forEach(function (table) {
        var host = table.closest(".jp-OutputArea-output") || table.parentNode;
        if (host.closest(".table-sheet")) return;
        var sheet = document.createElement("div");
        sheet.className = "table-sheet";
        host.parentNode.insertBefore(sheet, host);
        sheet.appendChild(host);
    });
    document.querySelectorAll(".jp-RenderedMarkdown table").forEach(function (table) {
        if (table.closest(".table-sheet")) return;
        var sheet = document.createElement("div");
        sheet.className = "table-sheet table-sheet-center";
        table.parentNode.insertBefore(sheet, table);
        sheet.appendChild(table);
    });

    function buildFeatureLookup(glossary, host) {
        var field = document.createElement("div");
        field.className = "feature-lookup-field";
        var searchRow = document.createElement("div");
        searchRow.className = "feature-lookup-search";
        var icon = document.createElement("span");
        icon.className = "feature-lookup-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M16 16l5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg>';
        var input = document.createElement("input");
        input.type = "text";
        input.className = "feature-lookup-input";
        input.setAttribute("autocomplete", "off");
        input.setAttribute("spellcheck", "false");
        input.placeholder = "Признак из таблицы (cal_logs)";
        var result = document.createElement("div");
        result.className = "feature-lookup-result";
        result.hidden = true;
        searchRow.appendChild(icon);
        searchRow.appendChild(input);
        field.appendChild(searchRow);
        field.appendChild(result);
        host.appendChild(field);

        var byLower = {};
        Object.keys(glossary).forEach(function (key) {
            byLower[key.toLowerCase()] = key;
        });

        function apply() {
            var raw = input.value.trim();
            field.classList.remove("is-match", "is-invalid");
            if (!raw) {
                result.hidden = true;
                result.textContent = "";
                return;
            }
            var key = byLower[raw.toLowerCase()];
            if (!key) {
                result.hidden = false;
                field.classList.add("is-invalid");
                result.innerHTML = '<p class="feature-lookup-miss">Нет такого признака в таблице</p>';
                return;
            }
            var item = glossary[key];
            field.classList.add("is-match");
            result.hidden = false;
            result.innerHTML =
                '<p class="feature-lookup-desc">' + item.description + "</p>"
                + '<p class="feature-lookup-kind">' + item.kind + "</p>";
        }

        input.addEventListener("change", apply);
        input.addEventListener("blur", apply);
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                apply();
            }
        });
    }

    if (page.sections && page.sections.length) {
        var right = document.createElement("aside");
        var box = document.createElement("div");
        var scroll = document.createElement("div");
        right.className = "sidebar page-toc";
        box.className = "sidebar-box page-toc-box";
        scroll.className = "page-toc-scroll";
        page.sections.forEach(function (section) {
            var link = document.createElement("a");
            link.href = section.href;
            link.textContent = section.title;
            scroll.appendChild(link);
        });
        box.appendChild(scroll);
        right.appendChild(box);
        if (page.featureLookup && page.featureGlossary && Object.keys(page.featureGlossary).length) {
            var lookupBox = document.createElement("div");
            lookupBox.className = "sidebar-box feature-lookup-box";
            buildFeatureLookup(page.featureGlossary, lookupBox);
            right.appendChild(lookupBox);
        }
        document.body.appendChild(right);
    }

    var sidebars = document.querySelectorAll(".sidebar");
    var tocBox = document.querySelector(".page-toc-scroll");
    var tocLinks = tocBox ? tocBox.querySelectorAll("a") : [];
    var headings = [];
    tocLinks.forEach(function (link) {
        var id = (link.getAttribute("href") || "").replace(/^#/, "");
        var heading = id ? document.getElementById(id) : null;
        if (heading) headings.push({ link: link, heading: heading });
    });
    var current = null;

    function restingTop() {
        var probe = sidebars[0];
        var previous = probe.style.top;
        probe.style.top = "";
        var top = probe.getBoundingClientRect().top;
        probe.style.top = previous;
        return top;
    }

    function markCurrent() {
        if (!headings.length || !tocBox) return;
        var line = document.querySelector(".topbar").offsetHeight + 48;
        var active = headings[0];
        var atBottom = window.scrollY > 0 && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 8;
        if (atBottom) {
            active = headings[headings.length - 1];
        } else {
            headings.forEach(function (item) {
                if (item.heading.getBoundingClientRect().top <= line) active = item;
            });
        }
        if (active !== current) {
            if (current) current.link.classList.remove("is-current");
            active.link.classList.add("is-current");
            current = active;
            var boxRect = tocBox.getBoundingClientRect();
            var linkRect = active.link.getBoundingClientRect();
            var delta = (linkRect.top + linkRect.height / 2) - (boxRect.top + boxRect.height / 2);
            tocBox.scrollTop += delta;
        }
    }

    function placeSidebar() {
        var limit = document.querySelector(".topbar").offsetHeight;
        var rest = restingTop();
        var top = rest - Math.min(window.scrollY, limit);
        sidebars.forEach(function (sidebar) {
            var lift = sidebar.classList.contains("page-toc") ? 80 : 0;
            sidebar.style.top = (top - lift) + "px";
        });
        var room = window.innerHeight - 2 * rest + 128;
        var maxFit = window.innerHeight - (rest - limit) - 16;
        var maxHeight = Math.max(160, Math.min(room, maxFit)) + "px";
        document.querySelectorAll(".sidebar-box").forEach(function (box) {
            if (box.classList.contains("feature-lookup-box")) {
                box.style.maxHeight = "";
                return;
            }
            box.style.maxHeight = maxHeight;
        });
        markCurrent();
    }
    window.addEventListener("scroll", placeSidebar);
    window.addEventListener("resize", placeSidebar);
    placeSidebar();

    var sun = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M12 2v2.2M12 19.8V22M2 12h2.2M19.8 12H22M4.8 4.8l1.6 1.6M17.6 17.6l1.6 1.6M19.2 4.8l-1.6 1.6M6.4 17.6l-1.6 1.6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg>';
    var moon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 14.5A8.5 8.5 0 1 1 9.5 3 7 7 0 0 0 21 14.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"></path></svg>';
    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "theme-toggle";
    function paintTheme() {
        var dark = document.documentElement.getAttribute("data-theme") === "dark";
        toggle.innerHTML = dark ? sun : moon;
        toggle.setAttribute("aria-label", dark ? "Светлая тема" : "Тёмная тема");
        if (document.body.classList.contains("jp-Notebook")) {
            document.body.setAttribute("data-jp-theme-light", dark ? "false" : "true");
        }
    }
    toggle.addEventListener("click", function () {
        var dark = document.documentElement.getAttribute("data-theme") === "dark";
        if (dark) {
            document.documentElement.removeAttribute("data-theme");
            localStorage.setItem("theme", "light");
        } else {
            document.documentElement.setAttribute("data-theme", "dark");
            localStorage.setItem("theme", "dark");
        }
        paintTheme();
    });
    document.body.appendChild(toggle);
    paintTheme();
});
</script>
"""


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