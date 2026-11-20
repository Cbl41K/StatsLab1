"""
Модуль для анализа, тестирования и визуализации генераторов случайных величин
в рамках лабораторной работы по статистике.
"""

from typing import Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from supporting_functions.data_structure import numericReview


def compare_statistics(
    original: Union[np.ndarray, pd.Series],
    generated: Union[np.ndarray, pd.Series],
    var_name: str = "cal_pka_basic",
) -> pd.DataFrame:
    """
    Сравнивает основные описательные статистики исходной и сгенерированной выборки
    с использованием функции numericReview, дополненной асимметрией и эксцессом.
    """
    orig_clean = np.asarray(original)[~np.isnan(np.asarray(original))]
    gen_clean = np.asarray(generated)[~np.isnan(np.asarray(generated))]

    df_orig = pd.DataFrame({var_name: orig_clean})
    df_gen = pd.DataFrame({f"{var_name}_gen": gen_clean})

    rev_orig = numericReview(df_orig).iloc[0]
    rev_gen = numericReview(df_gen).iloc[0]

    stats_dict = {
        "Объем выборки (n)": [len(orig_clean), len(gen_clean)],
        "Среднее (Mean)": [rev_orig["mean_value"], rev_gen["mean_value"]],
        "Медиана (Median)": [rev_orig["median_value"], rev_gen["median_value"]],
        "Станд. отклонение (Std)": [rev_orig["std"], rev_gen["std"]],
        "Квартиль 25% (Q25)": [rev_orig["Q25"], rev_gen["Q25"]],
        "Квартиль 75% (Q75)": [rev_orig["Q75"], rev_gen["Q75"]],
        "Межквартильный размах (IQR)": [rev_orig["iqr"], rev_gen["iqr"]],
        "Минимум (Min)": [orig_clean.min(), gen_clean.min()],
        "Максимум (Max)": [orig_clean.max(), gen_clean.max()],
        "Асимметрия (Skewness)": [stats.skew(orig_clean), stats.skew(gen_clean)],
        "Эксцесс (Kurtosis)": [stats.kurtosis(orig_clean), stats.kurtosis(gen_clean)],
    }

    comp_df = pd.DataFrame(stats_dict, index=["Исходные данные", "Сгенерированные данные"]).T

    # Вычисление разниц
    orig_vals = comp_df["Исходные данные"].astype(float)
    gen_vals = comp_df["Сгенерированные данные"].astype(float)
    comp_df["Абс. разность |Δ|"] = (gen_vals - orig_vals).abs()
    comp_df["Относит. погрешность (%)"] = np.where(
        orig_vals.abs() > 1e-6,
        ((gen_vals - orig_vals).abs() / orig_vals.abs()) * 100,
        np.nan,
    )

    return comp_df.round(4)


def plot_generator_comparison(
    original: Union[np.ndarray, pd.Series],
    generated: Union[np.ndarray, pd.Series],
    var_name: str = "cal_pka_basic",
) -> plt.Figure:
    """
    Строит комплексную 4-панельную визуализацию сравнения исходного
    и сгенерированного распределений:
    1) Наложение плотностей KDE и гистограмм
    2) Наложение эмпирических функций распределения (ECDF)
    3) Q-Q график (квантили исходных vs сгенерированных)
    4) Детальная гистограмма сгенерированных данных с ключевыми параметрами
    """
    orig_clean = np.asarray(original)[~np.isnan(np.asarray(original))]
    gen_clean = np.asarray(generated)[~np.isnan(np.asarray(generated))]

    sns.set_theme(style="whitegrid", palette="muted")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # --- 1. Плотности вероятности (KDE)
    ax1 = axes[0, 0]
    sns.kdeplot(orig_clean, color="#1f77b4", linewidth=2.4, label="Исходные данные (KDE)", ax=ax1)
    sns.kdeplot(gen_clean, color="#d95f02", linewidth=2.0, linestyle="--", label="Сгенерированные данные (KDE)", ax=ax1)
    ax1.set_title("Сравнение функций плотности вероятности (KDE)", fontsize=12, fontweight="bold")
    ax1.set_xlabel(f"Значение {var_name}")
    ax1.set_ylabel("Плотность вероятности")
    ax1.legend(loc="upper right")

    # --- 2. Эмпирические функции распределения (ECDF)
    ax2 = axes[0, 1]
    x_orig = np.sort(orig_clean)
    y_orig = np.arange(1, len(x_orig) + 1) / len(x_orig)
    x_gen = np.sort(gen_clean)
    y_gen = np.arange(1, len(x_gen) + 1) / len(x_gen)

    ax2.plot(x_orig, y_orig, color="#1f77b4", linewidth=2.2, label="Исходная ECDF")
    ax2.plot(x_gen, y_gen, color="#d95f02", linewidth=2.0, linestyle="--", label="Сгенерированная ECDF")
    ax2.axhline(0.5, color="gray", linestyle=":", alpha=0.7, label="Медиана (F=0.5)")
    ax2.set_title("Сравнение функций распределения (ECDF)", fontsize=12, fontweight="bold")
    ax2.set_xlabel(f"Значение {var_name}")
    ax2.set_ylabel("F(x)")
    ax2.legend(loc="lower right")

    # --- 3. Q-Q график (квантиль-квантиль)
    ax3 = axes[1, 0]
    percentiles = np.linspace(0.5, 99.5, 200)
    q_orig = np.percentile(orig_clean, percentiles)
    q_gen = np.percentile(gen_clean, percentiles)

    ax3.scatter(q_orig, q_gen, color="#2b5c8f", s=18, alpha=0.75, label="Квантили (0.5%–99.5%)")
    min_q = min(q_orig.min(), q_gen.min())
    max_q = max(q_orig.max(), q_gen.max())
    ax3.plot([min_q, max_q], [min_q, max_q], color="red", linestyle="--", linewidth=1.8, label="Идеальная прямая y = x")
    ax3.set_title("Q-Q график квантилей: Исходные vs Сгенерированные", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Квантили исходного распределения")
    ax3.set_ylabel("Квантили сгенерированного распределения")
    ax3.legend(loc="upper left")

    # --- 4. Гистограмма сгенерированных данных
    ax4 = axes[1, 1]
    sns.histplot(gen_clean, bins=50, stat="density", color="#a6bddb", edgecolor="white", ax=ax4, label="Гистограмма")
    sns.kdeplot(gen_clean, color="#045a8d", linewidth=2.0, ax=ax4, label="KDE")
    mean_val = np.mean(gen_clean)
    med_val = np.median(gen_clean)
    ax4.axvline(mean_val, color="red", linestyle="--", linewidth=1.8, label=f"Среднее = {mean_val:.2f}")
    ax4.axvline(med_val, color="green", linestyle="-", linewidth=1.8, label=f"Медиана = {med_val:.2f}")
    ax4.set_title("Гистограмма сгенерированных значений (n = len)", fontsize=12, fontweight="bold")
    ax4.set_xlabel(f"Значение {var_name}")
    ax4.set_ylabel("Плотность")
    ax4.legend(loc="upper right")

    plt.tight_layout()
    return fig


def test_distribution_fit(
    original: Union[np.ndarray, pd.Series],
    generated: Union[np.ndarray, pd.Series],
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Проверяет соответствие сгенерированной выборки исходному распределению
    с помощью двухвыборочных статистических критериев (Колмогоров-Смирнов, Вассерштейн).
    """
    orig_clean = np.asarray(original)[~np.isnan(np.asarray(original))]
    gen_clean = np.asarray(generated)[~np.isnan(np.asarray(generated))]

    # 1. Двухвыборочный критерий Колмогорова-Смирнова
    ks_stat, ks_p = stats.ks_2samp(orig_clean, gen_clean)

    # 2. Расстояние Вассерштейна (Earth Mover's Distance)
    wd_stat = stats.wasserstein_distance(orig_clean, gen_clean)

    # 3. Двухвыборочный критерий Крамера - фон Мизеса
    cvm_res = stats.cramervonmises_2samp(orig_clean, gen_clean)

    tests_data = [
        {
            "Статистический критерий": "Критерий Колмогорова–Смирнова (KS)",
            "Статистика": round(ks_stat, 5),
            "p-value": f"{ks_p:.4f}" if ks_p >= 1e-4 else f"{ks_p:.2e}",
            "Порог α": alpha,
            "Результат (H0: распределения равны)": "H0 принимается (распределения совпадают)" if ks_p >= alpha else "H0 отвергается",
        },
        {
            "Статистический критерий": "Критерий Крамера–фон Мизеса (CvM)",
            "Статистика": round(cvm_res.statistic, 5),
            "p-value": f"{cvm_res.pvalue:.4f}" if cvm_res.pvalue >= 1e-4 else f"{cvm_res.pvalue:.2e}",
            "Порог α": alpha,
            "Результат (H0: распределения равны)": "H0 принимается (распределения совпадают)" if cvm_res.pvalue >= alpha else "H0 отвергается",
        },
        {
            "Статистический критерий": "Расстояние Вассерштейна (EMD)",
            "Статистика": round(wd_stat, 5),
            "p-value": "— (метрика)",
            "Порог α": "—",
            "Результат (H0: распределения равны)": "Отличное соответствие (дистанция близка к 0)" if wd_stat < 0.1 else "Заметное расхождение",
        },
    ]

    return pd.DataFrame(tests_data).set_index("Статистический критерий")


def test_randomness(
    generated: Union[np.ndarray, pd.Series],
    max_lags: int = 25,
    alpha: float = 0.05,
) -> tuple[pd.DataFrame, plt.Figure]:
    """
    Проверяет случайность и независимость последовательности сгенерированных величин:
    - График и расчет автокорреляционной функции (АКФ) для лагов 1..max_lags
    - Доверительный интервал Бартлетта для белого шума (± 1.96 / sqrt(N))
    - Критерий серий Вальда-Вольфовица (Runs test) относительно медианы
    """
    gen_clean = np.asarray(generated)[~np.isnan(np.asarray(generated))]
    n = len(gen_clean)

    # 1. Автокорреляция для лагов 1..max_lags
    lags = np.arange(1, max_lags + 1)
    acf_values = [np.corrcoef(gen_clean[:-k], gen_clean[k:])[0, 1] for k in lags]
    ci_bound = 1.96 / np.sqrt(n)

    # 2. Критерий серий Вальда-Вольфовица относительно медианы
    median_val = np.median(gen_clean)
    signs = (gen_clean > median_val).astype(int)
    signs = signs[gen_clean != median_val]
    n1 = int((signs == 1).sum())
    n0 = int((signs == 0).sum())
    runs = 1 + int(np.diff(signs).astype(bool).sum())
    expected_runs = 1.0 + 2.0 * n1 * n0 / (n1 + n0)
    var_runs = (2.0 * n1 * n0 * (2.0 * n1 * n0 - n1 - n0)) / (((n1 + n0) ** 2) * (n1 + n0 - 1))
    z_runs = (runs - expected_runs) / np.sqrt(var_runs)
    p_runs = 2.0 * (1.0 - stats.norm.cdf(abs(z_runs)))

    is_uncorrelated = max(map(abs, acf_values)) <= (ci_bound + 1e-4)
    randomness_results = [
        {
            "Тест случайности": "Критерий серий Вальда–Вольфовица (Runs test)",
            "Параметр / Статистика": f"Runs = {runs}, E[R] = {expected_runs:.1f}, z = {z_runs:.3f}",
            "p-value": f"{p_runs:.4f}" if p_runs >= 1e-4 else f"{p_runs:.2e}",
            "Порог α": alpha,
            "Вывод": "Последовательность случайна (H0 принимается)" if p_runs >= alpha else "Зависимость обнаружена",
        },
        {
            "Тест случайности": f"Макс. автокорреляция (лаги 1..{max_lags})",
            "Параметр / Статистика": f"max |r| = {max(map(abs, acf_values)):.4f} (порог ±{ci_bound:.4f})",
            "p-value": "—",
            "Порог α": f"95% CI: ±{ci_bound:.4f}",
            "Вывод": "Автокорреляция отсутствует (белый шум)" if is_uncorrelated else "Есть слабая автокорреляция",
        },
    ]

    # График АКФ
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.stem(lags, acf_values, basefmt="k-", linefmt="C0-", markerfmt="C0o")
    ax.axhline(0, color="black", linewidth=1.0)
    ax.axhline(ci_bound, color="red", linestyle="--", linewidth=1.5, label=f"95% доверительная граница Бартлетта (±{ci_bound:.3f})")
    ax.axhline(-ci_bound, color="red", linestyle="--", linewidth=1.5)
    ax.set_title("Автокорреляционная функция (АКФ) сгенерированной последовательности", fontsize=12, fontweight="bold")
    ax.set_xlabel("Лаг k")
    ax.set_ylabel("Коэффициент автокорреляции r(k)")
    ax.set_ylim(-max(0.1, ci_bound * 2), max(0.1, ci_bound * 2))
    ax.legend(loc="upper right")
    plt.tight_layout()

    return pd.DataFrame(randomness_results).set_index("Тест случайности"), fig


def run_software_correctness_tests(generator_class, data: np.ndarray) -> pd.DataFrame:
    """
    Проверяет программную корректность реализации генератора:
    - Воспроизводимость при одинаковом random_state
    - Несовпадение при разных random_state
    - Валидация аргумента n (отрицательное число, ноль, float, неверный тип)
    - Проверка границ значений (отсутствие выбросов за x_min, x_max, отсутствие NaN/Inf)
    - Проверка генерации при малых (n=1) и больших объемах
    """
    checks = []

    # 1. Инициализация
    try:
        gen = generator_class(data)
        checks.append(("Инициализация объекта с корректными данными", "Успешно", "Пройден"))
    except Exception as e:
        checks.append(("Инициализация объекта с корректными данными", f"Ошибка: {e}", "Провален"))
        return pd.DataFrame(checks, columns=["Тест", "Детали", "Статус"]).set_index("Тест")

    # 2. Воспроизводимость
    s1 = gen.generate(100, random_state=42)
    s2 = gen.generate(100, random_state=42)
    is_reproducible = np.array_equal(s1, s2)
    checks.append((
        "Воспроизводимость (одинаковый seed дает идентичный массив)",
        "np.array_equal(s1, s2) == True",
        "Пройден" if is_reproducible else "Провален",
    ))

    # 3. Разные seed дают разные последовательности
    s3 = gen.generate(100, random_state=123)
    is_different = not np.array_equal(s1, s3)
    checks.append((
        "Разные seed дают различные случайные последовательности",
        "not np.array_equal(s1, s3) == True",
        "Пройден" if is_different else "Провален",
    ))

    # 4. Проверка формы и типа возвращаемого значения
    is_1d_numpy = isinstance(s1, np.ndarray) and s1.ndim == 1 and len(s1) == 100
    checks.append((
        "Формат результата: одномерный массив NumPy длины n",
        f"тип: {type(s1).__name__}, ndim: {s1.ndim}, len: {len(s1)}",
        "Пройден" if is_1d_numpy else "Провален",
    ))

    # 5. Обработка ошибки: n <= 0
    try:
        gen.generate(0)
        checks.append(("Обработка n = 0 (должен выбросить ValueError)", "Исключение не вызвано", "Провален"))
    except ValueError:
        checks.append(("Обработка n = 0 (должен выбросить ValueError)", "Выброшен ValueError", "Пройден"))
    except Exception as e:
        checks.append(("Обработка n = 0 (должен выбросить ValueError)", f"Выброшено не то исключение: {type(e).__name__}", "Провален"))

    try:
        gen.generate(-10)
        checks.append(("Обработка n < 0 (должен выбросить ValueError)", "Исключение не вызвано", "Провален"))
    except ValueError:
        checks.append(("Обработка n < 0 (должен выбросить ValueError)", "Выброшен ValueError", "Пройден"))
    except Exception as e:
        checks.append(("Обработка n < 0 (должен выбросить ValueError)", f"Выброшено не то исключение: {type(e).__name__}", "Провален"))

    # 6. Обработка ошибки: некорректный тип n
    try:
        gen.generate(15.5)  # float
        checks.append(("Обработка n типа float (должен выбросить TypeError)", "Исключение не вызвано", "Провален"))
    except TypeError:
        checks.append(("Обработка n типа float (должен выбросить TypeError)", "Выброшен TypeError", "Пройден"))
    except Exception as e:
        checks.append(("Обработка n типа float (должен выбросить TypeError)", f"Выброшено: {type(e).__name__}", "Провален"))

    # 7. Проверка границ диапазона и отсутствия NaN / Inf
    large_sample = gen.generate(10000, random_state=999)
    d_min, d_max = gen.x_min, gen.x_max
    in_bounds = (large_sample.min() >= d_min) and (large_sample.max() <= d_max)
    no_nan_inf = np.all(np.isfinite(large_sample))
    checks.append((
        "Физическая корректность: значения строго в диапазоне [x_min, x_max]",
        f"[{large_sample.min():.2f}; {large_sample.max():.2f}] ⊆ [{d_min:.2f}; {d_max:.2f}]",
        "Пройден" if in_bounds else "Провален",
    ))
    checks.append((
        "Отсутствие некорректных значений (NaN / Inf)",
        f"np.all(np.isfinite(sample)) == {no_nan_inf}",
        "Пройден" if no_nan_inf else "Провален",
    ))

    # 8. Граничный случай: n = 1
    s_single = gen.generate(1, random_state=1)
    is_single_ok = len(s_single) == 1 and np.isscalar(s_single[0])
    checks.append((
        "Граничный случай n = 1",
        f"len = {len(s_single)}, значение = {s_single[0]:.2f}",
        "Пройден" if is_single_ok else "Провален",
    ))

    return pd.DataFrame(checks, columns=["Тест", "Детали", "Статус"]).set_index("Тест")
