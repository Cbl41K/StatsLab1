"""
Модуль для статистического анализа параметра cal_pka_basic (основной pKa)
в рамках лабораторной работы по дисциплине «Статистика».
Служит для скрытия громоздкого кода из основного ноутбука.
"""

from pathlib import Path
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import PowerTransformer

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="muted")
RNG = np.random.default_rng(42)

# Настройка путей
def get_project_root() -> Path:
    """Определяет корень проекта StatsLab1."""
    direct = Path(__file__).resolve().parent.parent
    if (direct / "cleaned_data.csv").is_file():
        return direct
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "cleaned_data.csv").is_file():
            return candidate
        if (candidate / "StatsLab1" / "cleaned_data.csv").is_file():
            return candidate / "StatsLab1"
    return direct


def load_pka_data():
    """Загружает очищенные данные и извлекает cal_pka_basic."""
    root = get_project_root()
    df = pd.read_csv(root / "cleaned_data.csv")
    pka = df["cal_pka_basic"].dropna().to_numpy()
    
    n_total = len(df)
    n_valid = len(pka)
    n_missing = n_total - n_valid
    
    print(f"Всего молекул в базе: {n_total}")
    print(f"Заполнено cal_pka_basic: {n_valid} ({n_valid / n_total:.2%})")
    print(f"Пропусков: {n_missing} ({n_missing / n_total:.2%})")
    return df, pka


def plot_step1_stochastic(pka: np.ndarray):
    """Строит гистограмму распределения и функцию накопленной вероятности (ECDF)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))

    # 1. Плотность распределения (KDE)
    sns.histplot(pka, bins=45, kde=True, color="#2b5c8f", ax=axes[0], stat="density")
    axes[0].axvline(np.mean(pka), color="#d95f02", linestyle="--", linewidth=2, label=f"Среднее ({np.mean(pka):.2f})")
    axes[0].axvline(np.median(pka), color="#1b9e77", linestyle="-", linewidth=2, label=f"Медиана ({np.median(pka):.2f})")
    axes[0].set_title("Плотность распределения cal_pka_basic")
    axes[0].set_xlabel("Значение cal_pka_basic")
    axes[0].set_ylabel("Плотность")
    axes[0].legend()

    # 2. Эмпирическая функция распределения (ECDF)
    x_sorted = np.sort(pka)
    y_ecdf = np.arange(1, len(x_sorted) + 1) / len(x_sorted)
    axes[1].plot(x_sorted, y_ecdf, color="#2b5c8f", linewidth=2, label="ECDF (накопленная доля)")
    axes[1].axhline(0.5, color="gray", linestyle=":", label="Уровень 50% (медиана)")
    axes[1].axvline(np.median(pka), color="#1b9e77", linestyle="--", label=f"Медиана = {np.median(pka):.2f}")
    axes[1].set_title("Эмпирическая функция распределения (ECDF)")
    axes[1].set_xlabel("Значение cal_pka_basic")
    axes[1].set_ylabel("F(x)")
    axes[1].legend()

    plt.tight_layout()
    plt.show()



def analyze_step2_relationships(df: pd.DataFrame):
    """Исследует связь pKa с физиологическим зарядом и другими параметрами."""
    corr_targets = ["cal_physiological_charge", "cal_pka_acidic", "cal_logp"]
    corr_results = []

    for col in corr_targets:
        mask = df["cal_pka_basic"].notna() & df[col].notna()
        x = df.loc[mask, "cal_pka_basic"].to_numpy()
        y = df.loc[mask, col].to_numpy()

        p_stat, p_val = stats.pearsonr(x, y)
        s_stat, s_val = stats.spearmanr(x, y)
        corr_results.append({
            "Признак": col,
            "Пирсон r": round(p_stat, 3),
            "p-val (Пирсон)": f"{p_val:.2e}",
            "Спирмен r_s": round(s_stat, 3),
            "p-val (Спирмен)": f"{s_val:.2e}",
            "Связь значима (alpha=0.05)": "Да" if min(p_val, s_val) < 0.05 else "Нет"
        })  

    print("Связь cal_pka_basic с другими признаками:")
    print(pd.DataFrame(corr_results).set_index("Признак"))

    fig, ax = plt.subplots(figsize=(8, 5))

    # График: cal_pka_basic vs cal_pka_acidic
    mask_acid = df["cal_pka_basic"].notna() & df["cal_pka_acidic"].notna()
    hb = ax.hexbin(df.loc[mask_acid, "cal_pka_basic"], df.loc[mask_acid, "cal_pka_acidic"], gridsize=35, cmap="YlGnBu", mincnt=1)
    fig.colorbar(hb, ax=ax, label="Число молекул")
    ax.set_title("Плотность совместного распределения pKa basic и acidic")
    ax.set_xlabel("cal_pka_basic")
    ax.set_ylabel("cal_pka_acidic")

    plt.tight_layout()
    plt.show()


def analyze_step3_consistency(pka: np.ndarray):
    """Изучает сходимость выборочного среднего и медианы к параметрам базы."""
    sample_sizes = [10, 30, 100, 300, 1000, 3000, 9000]
    n_repeats = 300

    true_mean = np.mean(pka)
    true_median = np.median(pka)
    true_std = np.std(pka, ddof=0)

    means_by_size = {size: [] for size in sample_sizes}
    medians_by_size = {size: [] for size in sample_sizes}

    for size in sample_sizes:
        for _ in range(n_repeats):
            sample = RNG.choice(pka, size=size, replace=False)
            means_by_size[size].append(np.mean(sample))
            medians_by_size[size].append(np.median(sample))

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))

    # Выборочное среднее
    mean_data = [means_by_size[size] for size in sample_sizes]
    try:
        axes[0].boxplot(mean_data, tick_labels=sample_sizes, showfliers=False, patch_artist=True, boxprops=dict(facecolor="#a6bddb"))
    except TypeError:
        axes[0].boxplot(mean_data, labels=sample_sizes, showfliers=False, patch_artist=True, boxprops=dict(facecolor="#a6bddb"))
    axes[0].axhline(true_mean, color="red", linestyle="--", linewidth=2, label=f"Истинное среднее базы ({true_mean:.2f})")
    axes[0].set_title("Сходимость выборочного среднего")
    axes[0].set_xlabel("Размер случайной выборки n")
    axes[0].set_ylabel("Выборочное среднее")
    axes[0].legend()

    # Выборочная медиана
    median_data = [medians_by_size[size] for size in sample_sizes]
    try:
        axes[1].boxplot(median_data, tick_labels=sample_sizes, showfliers=False, patch_artist=True, boxprops=dict(facecolor="#ece7f2"))
    except TypeError:
        axes[1].boxplot(median_data, labels=sample_sizes, showfliers=False, patch_artist=True, boxprops=dict(facecolor="#ece7f2"))
    axes[1].axhline(true_median, color="red", linestyle="--", linewidth=2, label=f"Истинная медиана базы ({true_median:.2f})")
    axes[1].set_title("Сходимость выборочной медианы")
    axes[1].set_xlabel("Размер случайной выборки n")
    axes[1].set_ylabel("Выборочная медиана")
    axes[1].legend()

    plt.tight_layout()
    plt.show()

    table = pd.DataFrame({
        "Объём выборки n": sample_sizes,
        "Разброс среднего (эмпирический SE)": [np.std(means_by_size[s]) for s in sample_sizes],
        "Теоретический SE": [true_std / np.sqrt(s) for s in sample_sizes]
    }).round(3)
    print("Сравнение эмпирической погрешности среднего с формулой ЗБЧ:")
    print(table.set_index("Объём выборки n").to_string())


def analyze_step4_eda_and_transformation(df: pd.DataFrame, pka: np.ndarray):
    """Считает описательные статистики, проверяет выбросы и применение Йео-Джонсона."""
    q1, q3 = np.percentile(pka, [25, 75])
    summary = pd.Series({
        "Минимум": round(pka.min(), 2),
        "25% (первый квартиль Q1)": round(q1, 2),
        "Медиана": round(np.median(pka), 2),
        "Среднее": round(pka.mean(), 2),
        "75% (третий квартиль Q3)": round(q3, 2),
        "Максимум": round(pka.max(), 2),
        "Стандартное отклонение (σ)": round(pka.std(ddof=1), 2),
        "Асимметрия (Skewness)": round(stats.skew(pka), 2),
        "Эксцесс (Kurtosis)": round(stats.kurtosis(pka), 2),
        "Молекул с высоким pKa (> 12)": int((pka > 12).sum()),
    })
    print("Основные числовые показатели cal_pka_basic:")
    print(summary.to_frame(name="Значение").to_string())

    # метод Йео-Джонсона
    pt = PowerTransformer(method="yeo-johnson")
    pka_yj = pt.fit_transform(pka.reshape(-1, 1)).flatten()

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))

    # 1. Исходные данные с химическими границами
    sns.histplot(pka, bins=35, color="#2b5c8f", ax=axes[0])
    axes[0].axvline(0, color="gray", linestyle=":", label="Граница нейтральных (< 0)")
    axes[0].axvline(7.4, color="red", linestyle="--", label="Физиологический pH (7.4)")
    axes[0].set_title(f"Исходное распределение (асимметрия = {stats.skew(pka):.2f})")
    axes[0].set_xlabel("cal_pka_basic")
    axes[0].set_ylabel("Количество молекул")
    axes[0].legend()

    # 2. После преобразования Йео-Джонсона
    sns.histplot(pka_yj, bins=35, color="#3690c0", ax=axes[1])
    axes[1].set_title(f"После метода Йео-Джонсона (асимметрия = {stats.skew(pka_yj):.2f})")
    axes[1].set_xlabel("Преобразованные значения (шкала Йео-Джонсона)")
    axes[1].set_ylabel("Количество молекул")

    plt.tight_layout()
    plt.show()

    # 5 молекул с самым большим pKa
    top5 = df.nlargest(5, "cal_pka_basic")[["name", "cal_pka_basic", "cal_physiological_charge", "cal_molecular_weight"]]
    print("\nПримеры 5 молекул с наивысшим pKa:")
    print(top5.to_string(index=False))

def analyze_step5_sampling(pka: np.ndarray):
    """Сравнивает точность оценок с возвращением и без возвращения."""
    sub_sizes = [50, 200, 500, 1000, 2500, 5000, 7500, 9000]
    n_trials = 400
    true_std = np.std(pka, ddof=0)
    N = len(pka)

    se_with = []
    se_without = []

    for s in sub_sizes:
        m_with = [np.mean(RNG.choice(pka, size=s, replace=True)) for _ in range(n_trials)]
        m_without = [np.mean(RNG.choice(pka, size=s, replace=False)) for _ in range(n_trials)]
        se_with.append(np.std(m_with))
        se_without.append(np.std(m_without))

    fpc_theory = [true_std / np.sqrt(s) * np.sqrt((N - s) / (N - 1)) for s in sub_sizes]
    boot_theory = [true_std / np.sqrt(s) for s in sub_sizes]

    plt.figure(figsize=(10, 4.3))
    plt.plot(sub_sizes, se_with, "o--", color="#d95f02", label="С возвращением (эмпирический SE)")
    plt.plot(sub_sizes, boot_theory, "-", color="#d95f02", alpha=0.4, label="С возвращением (теория)")
    plt.plot(sub_sizes, se_without, "s--", color="#1b9e77", label="Без возвращения (эмпирический SE)")
    plt.plot(sub_sizes, fpc_theory, "-", color="#1b9e77", alpha=0.4, label="Без возвращения (теория с FPC)")
    plt.title("Стандартная ошибка среднего (SE): с возвращением vs без возвращения")
    plt.xlabel("Размер выборки n")
    plt.ylabel("Стандартная ошибка среднего (SE)")
    plt.legend()
    plt.tight_layout()
    plt.show()

    table = pd.DataFrame({
        "Объём выборки n": sub_sizes,
        "Доля от базы (%)": [round(s / N * 100, 1) for s in sub_sizes],
        "SE (с возвращением)": np.round(se_with, 3),
        "SE (без возвращения)": np.round(se_without, 3),
        "Выигрыш точности (SE без / с)": np.round(np.array(se_without) / np.array(se_with), 3)
    })
    print("Сравнение ошибок при разных способах выборки:")
    print(table.set_index("Объём выборки n").to_string())



def analyze_step6_models(pka: np.ndarray):
    """Сравнивает подгонку классических законов и моделей смеси GMM по AIC/BIC."""
    x_grid = np.linspace(-12, 22, 1000)
    n = len(pka)
    models = []

    # 1. Нормальное
    mu_norm, s_norm = stats.norm.fit(pka)
    ll_norm = np.sum(stats.norm.logpdf(pka, mu_norm, s_norm))
    aic_norm = 2 * 2 - 2 * ll_norm
    bic_norm = np.log(n) * 2 - 2 * ll_norm
    models.append({"Модель": "Одиночное нормальное (1 колокол)", "Параметров": 2, "AIC": aic_norm, "BIC": bic_norm})

    # 2. Логистическое
    loc_log, s_log = stats.logistic.fit(pka)
    ll_log = np.sum(stats.logistic.logpdf(pka, loc_log, s_log))
    aic_log = 2 * 2 - 2 * ll_log
    bic_log = np.log(n) * 2 - 2 * ll_log
    models.append({"Модель": "Логистическое (1 колокол)", "Параметров": 2, "AIC": aic_log, "BIC": bic_log})

    # 3. Стьюдента t
    df_t, loc_t, s_t = stats.t.fit(pka)
    ll_t = np.sum(stats.t.logpdf(pka, df_t, loc_t, s_t))
    aic_t = 2 * 3 - 2 * ll_t
    bic_t = np.log(n) * 3 - 2 * ll_t
    models.append({"Модель": "Стьюдента t (1 колокол)", "Параметров": 3, "AIC": aic_t, "BIC": bic_t})

    # 4. GMM (k=2)
    gmm2 = GaussianMixture(n_components=2, random_state=42).fit(pka.reshape(-1, 1))
    ll_gmm2 = gmm2.score(pka.reshape(-1, 1)) * n
    aic_gmm2 = 2 * 5 - 2 * ll_gmm2
    bic_gmm2 = np.log(n) * 5 - 2 * ll_gmm2
    models.append({"Модель": "Смесь Гауссиан (GMM, 2 колокола)", "Параметров": 5, "AIC": aic_gmm2, "BIC": bic_gmm2})

    # 5. GMM (k=3)
    gmm3 = GaussianMixture(n_components=3, random_state=42).fit(pka.reshape(-1, 1))
    ll_gmm3 = gmm3.score(pka.reshape(-1, 1)) * n
    aic_gmm3 = 2 * 8 - 2 * ll_gmm3
    bic_gmm3 = np.log(n) * 8 - 2 * ll_gmm3
    models.append({"Модель": "Смесь Гауссиан (GMM, 3 колокола)", "Параметров": 8, "AIC": aic_gmm3, "BIC": bic_gmm3})

    table = pd.DataFrame(models).sort_values("AIC").round(1)
    print("Сравнение математических моделей распределения (чем меньше AIC/BIC, тем лучше):")
    print(table.set_index("Модель").to_string())

    fig, axes = plt.subplots(1, 2, figsize=(15, 4.5))

    # Сравнение плотностей
    sns.histplot(pka, bins=50, stat="density", color="#e5e5e5", edgecolor="none", ax=axes[0], label="Данные (гистограмма)")
    axes[0].plot(x_grid, stats.norm.pdf(x_grid, mu_norm, s_norm), "--", color="red", linewidth=2, label="Одиночный Гаусс (1 колокол)")
    axes[0].plot(x_grid, np.exp(gmm2.score_samples(x_grid.reshape(-1, 1))), "-.", color="green", label="Смесь 2 колоколов")
    axes[0].plot(x_grid, np.exp(gmm3.score_samples(x_grid.reshape(-1, 1))), "-", color="blue", linewidth=2.2, label="Смесь 3 колоколов (лучшая)")
    axes[0].set_title("Подгонка моделей: один колокол vs смеси")
    axes[0].set_xlabel("cal_pka_basic")
    axes[0].set_ylabel("Плотность")
    axes[0].legend()

    # Декомпозиция GMM-3
    weights = gmm3.weights_
    means = gmm3.means_.flatten()
    covars = np.sqrt(gmm3.covariances_.flatten())
    order = np.argsort(means)

    labels = ["1. Нейтральные / слабые", "2. Ароматические основания", "3. Алифатические амины"]
    colors = ["#2b5c8f", "#7570b3", "#d95f02"]

    sns.histplot(pka, bins=50, stat="density", color="#f5f5f5", edgecolor="none", ax=axes[1])
    for rank, idx in enumerate(order):
        pdf = weights[idx] * stats.norm.pdf(x_grid, means[idx], covars[idx])
        axes[1].plot(x_grid, pdf, linewidth=2, color=colors[rank],
                     label=f"{labels[rank]}: вес {weights[idx]:.0%}, μ={means[idx]:.1f}, σ={covars[idx]:.1f}")
    axes[1].plot(x_grid, np.exp(gmm3.score_samples(x_grid.reshape(-1, 1))), "k:", linewidth=2, label="Итоговая сумма смеси")
    axes[1].set_title("Разложение смеси 3 колоколов на химические классы")
    axes[1].set_xlabel("cal_pka_basic")
    axes[1].set_ylabel("Плотность")
    axes[1].legend()

    plt.tight_layout()
    plt.show()


def p_str(p: float) -> str:
    """Форматирует p-value аналогично hbond_simple.ipynb."""
    return "< 1e-300" if p == 0 else (f"{p:.2e}" if p < 1e-4 else f"{p:.4f}")


def analyze_step7_hypothesis1_state(df: pd.DataFrame):
    """
    Гипотеза 1: Зависят ли cal_pka_basic и cal_pka_acidic от физического состояния (state).
    Графики и таблицы выполнены в точности как в hbond_simple.ipynb.
    """
    N = len(df)
    state_code = np.full(N, -1)
    state_code[df["state"].isna().to_numpy()] = 0
    state_code[(df["state"] == "liquid").to_numpy()] = 1
    state_code[(df["state"] == "solid").to_numpy()] = 2
    keep = state_code >= 0

    LABELS = {0: "0 — state пропущен", 1: "1 — liquid", 2: "2 — solid"}
    COLORS = {0: "#E69F00", 1: "#0072B2", 2: "#009E73"}  # оранжевый, синий, зелёный

    print(pd.Series({LABELS[g]: int((state_code == g).sum()) for g in (0, 1, 2)}, name="молекул").to_frame())

    valid_both = keep & df["cal_pka_basic"].notna() & df["cal_pka_acidic"].notna()
    pka_b = df.loc[valid_both, "cal_pka_basic"].to_numpy()
    pka_a = df.loc[valid_both, "cal_pka_acidic"].to_numpy()
    sc = state_code[valid_both]

    # --- График 1 (2x2 диаграмма рассеяния по группам, точно как в hbond_simple.ipynb)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9.5), sharex=True, sharey=True)
    ax = axes[0, 0]
    for g, size, alpha in ((2, 7, 0.25), (0, 9, 0.5), (1, 14, 0.9)):
        m = sc == g
        ax.scatter(pka_b[m], pka_a[m], s=size, alpha=alpha, color=COLORS[g], label=LABELS[g], linewidths=0)
    ax.set_title("Все группы вместе")
    ax.legend(markerscale=2)

    for ax, g in zip((axes[0, 1], axes[1, 0], axes[1, 1]), (0, 1, 2)):
        m = sc == g
        ax.scatter(pka_b[m], pka_a[m], s=8, alpha=0.4 if g != 1 else 0.9, color=COLORS[g], linewidths=0)
        ax.set_title(f"Группа {LABELS[g]} (n = {int(m.sum())})")

    for ax in axes[1]:
        ax.set_xlabel("cal_pka_basic (основной pKa)")
    for ax in axes[:, 0]:
        ax.set_ylabel("cal_pka_acidic (кислотный pKa)")
    plt.tight_layout()
    plt.show()

    # --- График 2 (1x2 распределения внутри каждой группы, точно как в hbond_simple.ipynb)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    for ax, col, name, (b_min, b_max) in zip(
        axes,
        ("cal_pka_basic", "cal_pka_acidic"),
        ("cal_pka_basic: основной pKa", "cal_pka_acidic: кислотный pKa"),
        ((-10, 22), (-12, 20))
    ):
        bins = np.linspace(b_min, b_max, 25)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        for g in (0, 1, 2):
            m = (state_code == g) & df[col].notna()
            vals = df.loc[m, col].to_numpy()
            counts, _ = np.histogram(vals, bins=bins)
            share = counts / len(vals)
            ax.plot(bin_centers, share, "o-", color=COLORS[g], label=LABELS[g], lw=1.6, ms=4)
        ax.set_xlabel(name)
        ax.set_ylabel("доля молекул группы")
        ax.set_title("Распределение внутри каждой группы")
        ax.legend()
    plt.tight_layout()
    plt.show()

    # Сводная таблица по группам
    group_rows = []
    for g in (0, 1, 2):
        mb = (state_code == g) & df["cal_pka_basic"].notna()
        ma = (state_code == g) & df["cal_pka_acidic"].notna()
        m_both = sc == g
        group_rows.append({
            "группа": LABELS[g],
            "n": int((state_code == g).sum()),
            "медиана basic": np.median(df.loc[mb, "cal_pka_basic"]),
            "среднее basic": df.loc[mb, "cal_pka_basic"].mean(),
            "медиана acidic": np.median(df.loc[ma, "cal_pka_acidic"]),
            "среднее acidic": df.loc[ma, "cal_pka_acidic"].mean(),
            "корреляция basic и acidic (Спирмен)": stats.spearmanr(pka_b[m_both], pka_a[m_both]).statistic,
        })
    group_table = pd.DataFrame(group_rows).set_index("группа").round(2)
    print("\nХарактеристики групп:")
    print(group_table)

    # 1) Критерий Краскела–Уоллиса для трёх групп
    kw_rows = []
    for col, name in (("cal_pka_basic", "cal_pka_basic"), ("cal_pka_acidic", "cal_pka_acidic")):
        samples = [df.loc[(state_code == g) & df[col].notna(), col].to_numpy() for g in (0, 1, 2)]
        H, p = stats.kruskal(*samples)
        n_all = sum(len(s) for s in samples)
        eps2 = (H - 3 + 1) / (n_all - 3)
        kw_rows.append({
            "величина": name,
            "H (Краскел–Уоллис)": round(H, 2),
            "p-value": p_str(p),
            "ε² (размер эффекта)": round(max(0, eps2), 4),
            "вывод": "различия есть (p < 0,05)" if p < 0.05 else "различий нет (p ≥ 0,05)",
        })
    print("\n1) Критерий Краскела–Уоллиса для трех групп:")
    print(pd.DataFrame(kw_rows).set_index("величина"))

    # 2) Таблица сопряженности по диапазонам (аналог Cell 36 в hbond_simple.ipynb)
    b_bins = pd.cut(df["cal_pka_basic"], [-np.inf, 0, 4, 8, 12, np.inf], labels=["<0", "0–4", "4–8", "8–12", "12+"])
    sub = pd.crosstab(pd.Series(b_bins[keep], name="cal_pka_basic"), pd.Series(state_code[keep], name="группа"))
    chi2, p_chi, dof, _ = stats.chi2_contingency(sub)
    v = np.sqrt(chi2 / (sub.values.sum() * (min(sub.shape) - 1)))
    shares = (sub.div(sub.sum(axis=1), axis=0) * 100).round(1)
    shares.columns = [f"% группы {g}" for g in shares.columns]
    shares.insert(0, "молекул", sub.sum(axis=1))
    print(f"\n2) cal_pka_basic по диапазонам: хи-квадрат = {chi2:.1f}, степеней свободы = {dof}, p = {p_str(p_chi)}, V Крамера = {v:.3f}")
    print(shares)

    # 3) Попарные сравнения Манна-Уитни с поправкой Холма
    g0 = df.loc[(state_code == 0) & df["cal_pka_basic"].notna(), "cal_pka_basic"].to_numpy()
    g1 = df.loc[(state_code == 1) & df["cal_pka_basic"].notna(), "cal_pka_basic"].to_numpy()
    g2 = df.loc[(state_code == 2) & df["cal_pka_basic"].notna(), "cal_pka_basic"].to_numpy()
    pairs = [("0 (пропуск)", "1 (liquid)", g0, g1),
             ("0 (пропуск)", "2 (solid)", g0, g2),
             ("1 (liquid)", "2 (solid)", g1, g2)]
    pair_res = []
    for name_a, name_b, arr_a, arr_b in pairs:
        u_stat, p_val = stats.mannwhitneyu(arr_a, arr_b)
        effect_r = 2 * u_stat / (len(arr_a) * len(arr_b)) - 1
        pair_res.append({
            "Сравнение": f"{name_a} vs {name_b}",
            "Медиана 1": round(np.median(arr_a), 2),
            "Медиана 2": round(np.median(arr_b), 2),
            "p-value": p_val,
            "Эффект r": round(effect_r, 3)
        })
    pair_df = pd.DataFrame(pair_res)
    order = pair_df["p-value"].argsort().to_numpy()
    holm = np.empty(len(pair_df))
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (len(pair_df) - rank) * pair_df["p-value"].iloc[idx])
        holm[idx] = min(1.0, running)
    pair_df["p с поправкой Холма"] = holm
    pair_df["Различие значимо"] = np.where(pair_df["p с поправкой Холма"] < 0.05, "Да", "Нет")
    pair_df["p-value"] = pair_df["p-value"].apply(lambda p: f"{p:.4f}")
    pair_df["p с поправкой Холма"] = pair_df["p с поправкой Холма"].apply(lambda p: f"{p:.4f}")
    print("\n3) Попарные сравнения Манна–Уитни для cal_pka_basic с поправкой Холма:")
    print(pair_df.set_index("Сравнение"))


def analyze_step7_hypothesis2_interchangeability(df: pd.DataFrame):
    """
    Гипотеза 2: Можно ли заменить cal_pka_basic на cal_pka_acidic (и наоборот).
    Графики и таблицы выполнены в точности как в hbond_simple.ipynb (раздел 2).
    """
    valid = df["cal_pka_basic"].notna() & df["cal_pka_acidic"].notna()
    a = df.loc[valid, "cal_pka_basic"].to_numpy()
    d = df.loc[valid, "cal_pka_acidic"].to_numpy()
    N = len(a)

    core = (a >= np.percentile(a, 1)) & (a <= np.percentile(a, 99)) & \
           (d >= np.percentile(d, 1)) & (d <= np.percentile(d, 99))

    def bootstrap_ci(func, x, y, n_boot=1000):
        values = []
        for _ in range(n_boot):
            idx = RNG.integers(0, len(x), len(x))
            values.append(func(x[idx], y[idx]))
        return np.percentile(values, [2.5, 97.5])

    pearson_f = lambda x, y: np.corrcoef(x, y)[0, 1]
    spearman_f = lambda x, y: stats.spearmanr(x, y).statistic

    rows = []
    for label, x, y in (("Спирмен (все данные) — основной", a, d),
                        ("Пирсон (все данные)", a, d),
                        ("Пирсон (без крайнего 1%)", a[core], d[core])):
        is_spearman = label.startswith("Спирмен")
        res = stats.spearmanr(x, y) if is_spearman else stats.pearsonr(x, y)
        lo, hi = bootstrap_ci(spearman_f if is_spearman else pearson_f, x, y)
        rows.append({
            "коэффициент": label,
            "значение": round(res.statistic, 3),
            "95% доверительный интервал": f"[{lo:.3f}; {hi:.3f}]",
            "p-value": p_str(res.pvalue)
        })
    print("\nКорреляция cal_pka_basic и cal_pka_acidic:")
    print(pd.DataFrame(rows).set_index("коэффициент"))

    def regression_report(x, y, k=5):
        fit = stats.linregress(x, y)
        order = RNG.permutation(len(x))
        pred = np.empty(len(x))
        for fold in np.array_split(order, k):
            train = np.setdiff1d(order, fold)
            slope, intercept = np.polyfit(x[train], y[train], 1)
            pred[fold] = intercept + slope * x[fold]
        err = y - pred
        q1, q3 = np.percentile(y, [25, 75])
        return {
            "наклон b1": fit.slope, "сдвиг b0": fit.intercept,
            "R²": 1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum(),
            "MAE": np.abs(err).mean(), "RMSE": np.sqrt((err ** 2).mean()),
            "σ исходной": y.std(ddof=0), "IQR исходной": q3 - q1,
            "RMSE / σ": np.sqrt((err ** 2).mean()) / y.std(ddof=0),
            "MAE / IQR": np.abs(err).mean() / (q3 - q1),
            "в пределах ±1": (np.abs(pred - y) <= 1).mean(),
        }, pred

    rep_ad, pred_d = regression_report(a, d)  # basic -> acidic
    rep_da, pred_a = regression_report(d, a)  # acidic -> basic
    rep_ad_core, _ = regression_report(a[core], d[core])
    rep_da_core, _ = regression_report(d[core], a[core])

    # --- График 3: Диаграмма рассеяния с прямой и график остатков (как Cell 42 в hbond_simple.ipynb)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax = axes[0]
    ax.scatter(a, d, s=5, alpha=0.15, color="C0", linewidths=0, label="молекулы")
    bins_a = np.linspace(-10, 22, 20)
    b_idx = np.digitize(a, bins_a)
    means_x, means_y = [], []
    for i in range(1, len(bins_a)):
        m = b_idx == i
        if m.sum() >= 10:
            means_x.append(a[m].mean())
            means_y.append(d[m].mean())
    ax.plot(means_x, means_y, "s", color="C3", ms=4, label="среднее acidic при данном basic")
    xs = np.array([-10, 22])
    ax.plot(xs, rep_ad["сдвиг b0"] + rep_ad["наклон b1"] * xs, "k-", lw=2,
            label=f"МНК: acidic = {rep_ad['сдвиг b0']:.2f} + {rep_ad['наклон b1']:.2f}·basic")
    ax.set_xlabel("basic (основной pKa)")
    ax.set_ylabel("acidic (кислотный pKa)")
    ax.set_title("Диаграмма рассеяния и линейная регрессия")
    ax.legend(loc="upper left")

    ax = axes[1]
    resid = d - pred_d
    ax.scatter(a, resid, s=5, alpha=0.15, color="C1", linewidths=0)
    ax.axhline(0, color="k", lw=1.2)
    ax.set_xlabel("basic (основной pKa)")
    ax.set_ylabel("ошибка прогноза acidic (факт − прогноз)")
    ax.set_title("Ошибки прогноза")
    plt.tight_layout()
    plt.show()

    # --- График 4: Сравнение исходного распределения и распределения заменителя (как Cell 44 в hbond_simple.ipynb)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    for ax, y, pred, name, (b_min, b_max) in (
        (axes[0], d, pred_d, "acidic (кислотный), прогноз по basic", (-12, 20)),
        (axes[1], a, pred_a, "basic (основной), прогноз по acidic", (-10, 22))
    ):
        bins = np.linspace(b_min, b_max, 25)
        w = (bins[1] - bins[0]) * 0.4
        centers = (bins[:-1] + bins[1:]) / 2
        c_real, _ = np.histogram(y, bins=bins)
        c_pred, _ = np.histogram(pred, bins=bins)
        ax.bar(centers - w/2, c_real / N, width=w, color="C7", label="настоящие значения")
        ax.bar(centers + w/2, c_pred / N, width=w, color="C3", label="предсказанные")
        ax.set_xlabel("значение pKa")
        ax.set_ylabel("доля молекул")
        ax.set_title(name)
        ax.legend()
    plt.tight_layout()
    plt.show()

    swap_rows = {}
    for label, rep in (("basic → acidic (все данные)", rep_ad), ("acidic → basic (все данные)", rep_da),
                       ("basic → acidic (без крайнего 1%)", rep_ad_core), ("acidic → basic (без крайнего 1%)", rep_da_core)):
        swap_rows[label] = {
            "σ исходной": rep["σ исходной"], "IQR исходной": rep["IQR исходной"],
            "RMSE": rep["RMSE"], "RMSE / σ": rep["RMSE / σ"],
            "MAE": rep["MAE"], "MAE / IQR": rep["MAE / IQR"],
            "потеряно дисперсии (1 − R²)": 1 - rep["R²"],
            "прогноз в пределах ±1": rep["в пределах ±1"],
        }
    swap_table = pd.DataFrame(swap_rows).T.round(2)
    print("\nОценка взаимозаменяемости:")
    print(swap_table)


def analyze_step7_hypothesis4_multimodal(pka: np.ndarray):
    """
    Гипотеза 4: Одновершинная модель vs модель смеси GMM.
    Критерий: Тест отношения правдоподобия (LRT).
    """
    n = len(pka)
    # 1 колокол
    mu, s = stats.norm.fit(pka)
    ll_1 = np.sum(stats.norm.logpdf(pka, mu, s))

    # 3 колокола (GMM)
    gmm = GaussianMixture(n_components=3, random_state=42).fit(pka.reshape(-1, 1))
    ll_3 = gmm.score(pka.reshape(-1, 1)) * n

    # Тест отношения правдоподобия: LRT = 2 * (ll_3 - ll_1) ~ chi2(df = 8 - 2 = 6)
    lr_stat = 2 * (ll_3 - ll_1)
    df_diff = 6
    p_val = stats.chi2.sf(lr_stat, df_diff)

    fig, ax = plt.subplots(figsize=(8, 3.8))
    x_grid = np.linspace(-10, 20, 500)
    sns.histplot(pka, bins=45, stat="density", color="#e5e5e5", ax=ax, label="Данные")
    ax.plot(x_grid, stats.norm.pdf(x_grid, mu, s), "--", color="red", linewidth=2, label="H0: Одновершинная модель (Гаусс)")
    ax.plot(x_grid, np.exp(gmm.score_samples(x_grid.reshape(-1, 1))), "-", color="blue", linewidth=2.2, label="H1: Смесь 3 колоколов (GMM)")
    ax.set_title("Проверка гипотезы 4: Одиночный колокол vs Смесь")
    ax.set_xlabel("cal_pka_basic")
    ax.set_ylabel("Плотность")
    ax.legend()
    plt.tight_layout()
    plt.show()

    print(f"Статистика теста отношения правдоподобия: LR = {lr_stat:.1f} (df = {df_diff})")
    print(f"p-value: {'< 1e-100' if p_val < 1e-100 else f'{p_val:.4e}'}")
    print(f"Решение (α = 0.05): {'H0 отвергается, распределение строго многовершинно' if p_val < 0.05 else 'H0 принимается'}")

