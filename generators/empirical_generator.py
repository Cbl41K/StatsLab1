"""Генератор случайных величин на основе эмпирической функции распределения.

Метод обратной функции (inverse transform sampling): эмпирическая функция
распределения (ЭФР) строится через индикаторную функцию

    F_n(x) = (1/n) * sum_{i=1..n} 1{x_i <= x},

а значения генерируются как F_n^{-1}(U), где U ~ Uniform(0, 1) и

    F_n^{-1}(u) = inf{ x : F_n(x) >= u }.
"""
from numbers import Integral

import numpy as np

from generators.base_generator import BaseGenerator


class EmpiricalCDFGenerator(BaseGenerator):
    """Генератор по ЭФР исходной выборки (метод обратной функции).

    Все параметры распределения вычисляются один раз в ``__init__``:

    support_ : отсортированные различные значения выборки s_1 < ... < s_m
    pmf_     : вероятности p_k = (число x_i, равных s_k) / n
    cdf_     : значения ЭФР в точках носителя, F_n(s_k) = p_1 + ... + p_k
    n_       : объём исходной выборки

    Метод ``generate`` только берёт случайные числа U ~ Uniform(0, 1) и
    находит для каждого наименьшее k, при котором F_n(s_k) >= U.
    """

    def __init__(self, data):
        super().__init__(data)  # BaseGenerator: данные одномерны и непусты
        values = self.data

        if not np.issubdtype(values.dtype, np.number) or np.issubdtype(
            values.dtype, np.complexfloating
        ):
            raise TypeError(
                f"Data must be real numbers, got dtype {values.dtype}"
            )
        if not np.all(np.isfinite(values)):
            raise ValueError("Data must not contain NaN or infinite values")

        sorted_data = np.sort(values)
        self.n_ = sorted_data.size
        self.support_ = np.unique(sorted_data)
        # Индикаторная функция: число элементов выборки с x_i <= s_k
        counts_le = np.searchsorted(sorted_data, self.support_, side="right")
        self.cdf_ = counts_le / self.n_                       # F_n(s_k); последний элемент ровно 1.0
        self.pmf_ = np.diff(counts_le, prepend=0) / self.n_   # p_k

    # ------------------------------------------------------------------ ЭФР и обратная функция
    def cdf(self, x):
        """Значение ЭФР: F_n(x) = доля элементов выборки, не превосходящих x."""
        x = np.asarray(x, dtype=float)
        if np.any(np.isnan(x)):
            raise ValueError("x must not contain NaN")
        k = np.searchsorted(self.support_, x, side="right")   # сколько точек носителя <= x
        return np.concatenate(([0.0], self.cdf_))[k]

    def ppf(self, u):
        """Обратная функция F_n^{-1}(u) = inf{x : F_n(x) >= u}, u из [0, 1]."""
        u = np.asarray(u, dtype=float)
        if np.any(np.isnan(u)) or np.any(u < 0) or np.any(u > 1):
            raise ValueError("u must be in the interval [0, 1]")
        return self.support_[np.searchsorted(self.cdf_, u, side="left")]

    # ------------------------------------------------------------------ генерация
    @staticmethod
    def _check_n(n):
        if isinstance(n, (bool, np.bool_)) or not isinstance(n, Integral):
            raise TypeError(f"n must be an integer, got {type(n).__name__}")
        if n < 0:
            raise ValueError(f"n must be non-negative, got {n}")
        return int(n)

    def generate(self, n: int, random_state=None) -> np.ndarray:
        """Сгенерировать n значений.

        n            : неотрицательное целое число
        random_state : None, неотрицательное целое (seed) или numpy.random.Generator.
                       При фиксированном целом seed результат всегда один и тот же.
        Возвращает одномерный массив numpy длины n с тем же dtype, что у исходных данных.
        """
        n = self._check_n(n)
        rng = np.random.default_rng(random_state)
        u = rng.random(n)                                      # U ~ Uniform[0, 1)
        return self.support_[np.searchsorted(self.cdf_, u, side="left")]

    def __repr__(self):
        return (
            f"{type(self).__name__}(n={self.n_}, unique_values={self.support_.size}, "
            f"min={self.support_[0]}, max={self.support_[-1]})"
        )
