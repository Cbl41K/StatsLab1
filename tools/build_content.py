from pathlib import Path

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

CHEMIST = (
    "Исследует свойства молекул и разрабатывает свою часть статистического анализа: "
    "смотрит, как устроены величины, как они связаны, и проверяет гипотезы."
)

KICKER = "Лабораторная работа 01"
TITLE = "Инфохимия. Статистический анализ свойств молекул"

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
<p>Создание генераторов (на основе базового генератора) соответствующих случайных величин, рассмотренных в предыдущем спринте, и сравнение с тем, что было в исходной выборке; дальнейшие выводы по выполненной работе.</p>
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

INTRO = """
<p><strong>Этот репозиторий и сайт</strong> Материалы лабораторной по инфохимии: статистический анализ свойств молекул на реальных данных. Здесь собраны очищенный датасет, ноутбуки с расчётами, выводами и графиками, а также страницы для чтения без запуска кода. Задача работы — рассмотреть числовые характеристики веществ как случайные величины: оценить распределения, связи, выборки и гипотезы, а затем перейти к моделированию.</p>
<p><strong>Исходные данные</strong> Выборка из базы DrugBank: лекарственные соединения и заранее посчитанные для них дескрипторы (молекулярные признаки). После очистки от экспериментальных признаков и служебных полей остаются тысячи строк; каждая строка — одна молекула, каждый столбец — одна числовая (или категориальная) характеристика, пригодная для статистики. Именно с этим набором команда выполняет последующую работу.</p>
<p><strong>Спринт 1 — анализ</strong> Сначала идёт обзор всего датасета: пропуски, распределения, корреляции, план дальнейших разборов. Затем в отдельных ноутбуках команда разбирает выбранные пары признаков по единому плану: обосновывает стохастику (случайность), проверяет зависимости, выполняет анализ и формулирует итоги.</p>
<p><strong>Спринт 2 — генератор</strong> Команда реализует генераторы случайных величин по эмпирическим или теоретическим распределениям данных первого спринта: у каждого свой метод, общий интерфейс (BaseGenerator, инициализация по данным), сравнение с исходным распределением на графиках и по статистикам, статистические тесты и выводы о качестве.</p>
<p>Главная страница расчётов не содержит: она объясняет устройство работы и порядок чтения. В ноутбуках код свёрнут под пунктом «Код», графики под пунктом «Графики». Слева — меню по всей работе, справа — оглавление открытой страницы.</p>
"""
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

