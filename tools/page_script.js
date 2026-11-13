document.addEventListener("DOMContentLoaded", function () {
    var page = window.PAGE_CHROME;
    var bar = document.createElement("div");
    var layout = document.createElement("div");
    var aside = document.createElement("aside");
    var content = document.createElement("div");

    bar.className = "topbar";
    bar.innerHTML = "<p class=\"kicker\"></p><h1></h1>";
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
            if (section.level && section.level > 2) {
                link.style.paddingLeft = (section.level - 2) * 0.65 + "rem";
                link.style.fontSize = section.level >= 4 ? "0.92em" : "";
            }
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
