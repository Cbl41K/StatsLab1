import numpy as np

from .base_generator import BaseGenerator


_MIXTURE_PARAMETERS = np.asarray(
    [0.41664809549588855, -3.270312984628837, 4.3868098134404825, 0.3104969669770016, 4.602998722849734, 7.069252981284711, 0.27285493752711, 9.251727602672272, 1.7807129066793415],
    dtype=np.float64,
)


class _WeightSumGenerator(BaseGenerator):
    def __init__(self, mixture_parameters: np.ndarray):
        super().__init__(mixture_parameters)

    def generate(self, n: int, random_state=None) -> np.ndarray:
        components = self.data.reshape(-1, 3)
        rng = np.random.default_rng(random_state)
        selected = rng.choice(
            components.shape[0],
            size=n,
            p=components[:, 0],
        )
        return rng.normal(
            loc=components[selected, 1],
            scale=np.sqrt(components[selected, 2]),
        )


def weight_sum_generator(
    volume: int,
    seed: int,
    mixture_parameters: np.ndarray = _MIXTURE_PARAMETERS,
) -> np.ndarray:
    return _WeightSumGenerator(mixture_parameters).generate(
        volume, random_state=seed
    )