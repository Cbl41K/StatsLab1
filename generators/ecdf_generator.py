from typing import Optional, Union
import numpy as np
from generators.base_generator import BaseGenerator


class EcdfContinuousGenerator(BaseGenerator):
    """
    Генератор случайной величины на основе эмпирической функции распределения
    (ЭФР) с кусочно-линейной интерполяцией для непрерывных величин.

    Метод моделирования: Inverse Transform Sampling (метод обратной функции).
    Для непрерывной случайной величины ступени дискретной ЭФР заменяются
    линейной интерполяцией между порядковыми статистиками выборки, что
    обеспечивает непрерывную плотность и генерацию любых вещественных значений
    в пределах выборочного диапазона [x_min, x_max].
    """

    def __init__(self, data):
        # Предобработка: фильтрация пропусков NaN
        raw = np.asarray(data)
        if np.issubdtype(raw.dtype, np.number):
            clean_data = raw[~np.isnan(raw)]
        else:
            clean_data = raw

        # Инициализация базового класса (проверка одномерности и непустоты)
        super().__init__(clean_data)

        # Все ресурсоемкие вычисления производятся ОДИН раз при инициализации объекта
        self.x_sorted = np.sort(self.data)
        self.n_samples = len(self.x_sorted)

        # Сетка вероятностей [0.0, 1.0] для кусочно-линейной квантильной функции.
        # Связывает минимум x_(1) с вероятностью 0.0 и максимум x_(N) с 1.0.
        self.probabilities = np.linspace(0.0, 1.0, self.n_samples)

        self.x_min = float(self.x_sorted[0])
        self.x_max = float(self.x_sorted[-1])

    def generate(
        self, n: int, random_state: Optional[Union[int, np.random.Generator]] = None
    ) -> np.ndarray:
        """
        Генерирует n псевдослучайных величин.

        Параметры:
        ----------
        n : int
            Количество генерируемых значений. Должно быть строго положительным целым числом.
        random_state : int, np.random.Generator или None
            Зерно генератора случайных чисел для воспроизводимости.

        Возвращает:
        -----------
        samples : np.ndarray
            Одномерный массив сгенерированных значений.
        """
        if not isinstance(n, (int, np.integer)) or isinstance(n, bool):
            raise TypeError(f"Параметр n должен быть целым числом, получено {type(n).__name__}")
        if n <= 0:
            raise ValueError(f"Параметр n должен быть строго положительным числом, получено {n}")

        rng = np.random.default_rng(random_state)
        u = rng.uniform(0.0, 1.0, size=n)
        samples = np.interp(u, self.probabilities, self.x_sorted)
        return samples

    def ppf(self, q: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Квантильная функция (обратная ЭФР с интерполяцией): x = Q(q)."""
        q_arr = np.asarray(q)
        if np.any((q_arr < 0.0) | (q_arr > 1.0)):
            raise ValueError("Вероятности q должны лежать на отрезке [0, 1]")
        res = np.interp(q_arr, self.probabilities, self.x_sorted)
        return float(res) if np.isscalar(q) else res

    def cdf(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Непрерывная эмпирическая функция распределения: q = F(x)."""
        x_arr = np.asarray(x)
        res = np.interp(x_arr, self.x_sorted, self.probabilities)
        return float(res) if np.isscalar(x) else res

