import numpy as np

from .base_generator import BaseGenerator


_COMPONENT_COUNT = 3
_EM_MAX_ITERATIONS = 1000
_ROOT_MAX_ITERATIONS = 64


def _log_component_densities(
    values: np.ndarray,
    weights: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
) -> np.ndarray:
    offsets = values[:, None] - means[None, :]
    return (
        np.log(weights)[None, :]
        - 0.5 * np.log(2.0 * np.pi * variances)[None, :]
        - 0.5 * offsets**2 / variances[None, :]
    )


def _find_roots(function, grid: np.ndarray) -> np.ndarray:
    values = function(grid)
    crossings = np.flatnonzero(
        ((values[:-1] < 0) & (values[1:] > 0))
        | ((values[:-1] > 0) & (values[1:] < 0))
    )
    roots = []

    for index in crossings:
        left = grid[index]
        right = grid[index + 1]
        left_value = values[index]

        for _ in range(_ROOT_MAX_ITERATIONS):
            midpoint = left + (right - left) / 2.0
            midpoint_value = function(np.asarray([midpoint]))[0]
            if midpoint_value == 0.0:
                left = right = midpoint
                break
            if (left_value < 0) == (midpoint_value < 0):
                left = midpoint
                left_value = midpoint_value
            else:
                right = midpoint

        roots.append(left + (right - left) / 2.0)

    return np.asarray(roots, dtype=np.float64)


class RatioOfUniformsGenerator(BaseGenerator):
    """Generate samples from a fitted three-component Gaussian mixture."""

    def __init__(self, data):
        super().__init__(data)

        values = np.asarray(self.data, dtype=np.float64)
        values = values[np.isfinite(values)]
        if values.size < _COMPONENT_COUNT:
            raise ValueError("Data must contain at least three finite values")
        if np.ptp(values) == 0.0:
            raise ValueError("Data must contain more than one distinct value")

        self.weights, self.means, self.variances = self._fit_mixture(values)
        self._standard_deviations = np.sqrt(self.variances)
        self.u_max, self.v_min, self.v_max = self._calculate_bounds()

    @staticmethod
    def _fit_mixture(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Fit three univariate normal components once using the EM algorithm."""
        means = np.quantile(values, [1.0 / 6.0, 0.5, 5.0 / 6.0])
        global_variance = np.var(values)
        variance_floor = max(
            global_variance * 1e-8,
            np.finfo(np.float64).eps * max(1.0, np.max(np.abs(values))) ** 2,
        )
        weights = np.full(_COMPONENT_COUNT, 1.0 / _COMPONENT_COUNT)
        variances = np.full(_COMPONENT_COUNT, max(global_variance, variance_floor))
        previous_log_likelihood = -np.inf

        for _ in range(_EM_MAX_ITERATIONS):
            log_densities = _log_component_densities(
                values, weights, means, variances
            )
            row_maxima = np.max(log_densities, axis=1, keepdims=True)
            unnormalized = np.exp(log_densities - row_maxima)
            responsibilities = unnormalized / np.sum(
                unnormalized, axis=1, keepdims=True
            )

            effective_counts = np.sum(responsibilities, axis=0)
            weights = effective_counts / values.size
            means = np.sum(responsibilities * values[:, None], axis=0) / effective_counts
            offsets = values[:, None] - means[None, :]
            variances = np.sum(responsibilities * offsets**2, axis=0) / effective_counts
            variances = np.maximum(variances, variance_floor)

            updated_log_densities = _log_component_densities(
                values, weights, means, variances
            )
            updated_maxima = np.max(updated_log_densities, axis=1)
            log_likelihood = np.sum(
                updated_maxima
                + np.log(
                    np.sum(
                        np.exp(updated_log_densities - updated_maxima[:, None]),
                        axis=1,
                    )
                )
            )
            if (
                np.isfinite(previous_log_likelihood)
                and abs(log_likelihood - previous_log_likelihood)
                <= 1e-8 * (1.0 + abs(previous_log_likelihood))
            ):
                break
            previous_log_likelihood = log_likelihood

        order = np.argsort(means)
        return weights[order], means[order], variances[order]

    def _density_and_derivative(
        self, x: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        offsets = x[..., None] - self.means
        component_densities = (
            self.weights
            * np.exp(-0.5 * offsets**2 / self.variances)
            / (np.sqrt(2.0 * np.pi) * self._standard_deviations)
        )
        density = np.sum(component_densities, axis=-1)
        derivative = np.sum(
            component_densities * (-offsets / self.variances), axis=-1
        )
        return density, derivative

    def _search_grid(self, lower: float, upper: float) -> np.ndarray:
        if lower == upper:
            return np.asarray([lower], dtype=np.float64)

        pieces = [np.linspace(lower, upper, 8193)]
        for mean, standard_deviation in zip(
            self.means, self._standard_deviations
        ):
            local = np.linspace(
                mean - 12.0 * standard_deviation,
                mean + 12.0 * standard_deviation,
                1025,
            )
            pieces.append(local[(local >= lower) & (local <= upper)])
        return np.unique(np.concatenate(pieces))

    def _calculate_bounds(self) -> tuple[float, float, float]:
        # The density's stationary points lie between the component means.
        density_grid = self._search_grid(float(self.means[0]), float(self.means[-1]))
        density_roots = _find_roots(
            lambda x: self._density_and_derivative(x)[1], density_grid
        )
        density_candidates = np.concatenate(
            (density_grid[[0, -1]], self.means, density_roots)
        )
        maximum_density = np.max(self._density_and_derivative(density_candidates)[0])
        u_max = np.nextafter(np.sqrt(maximum_density), np.inf)

        # For g(x)=x*sqrt(f(x)), stationary points satisfy 2f(x)+x*f'(x)=0.
        discriminant = np.hypot(self.means, np.sqrt(8.0 * self.variances))
        negative_component_roots = np.where(
            self.means >= 0.0,
            -4.0 * self.variances / (discriminant + self.means),
            (self.means - discriminant) / 2.0,
        )
        positive_component_roots = np.where(
            self.means >= 0.0,
            (self.means + discriminant) / 2.0,
            4.0 * self.variances / (discriminant - self.means),
        )
        lower = float(np.min(negative_component_roots))
        upper = float(np.max(positive_component_roots))
        ratio_grid = self._search_grid(lower, upper)
        ratio_grid = np.unique(
            np.concatenate(
                (ratio_grid, negative_component_roots, positive_component_roots, [0.0])
            )
        )

        def ratio_derivative_numerator(x):
            density, derivative = self._density_and_derivative(x)
            return 2.0 * density + x * derivative

        ratio_roots = _find_roots(ratio_derivative_numerator, ratio_grid)
        ratio_candidates = np.concatenate(
            (ratio_grid, ratio_roots, [lower, upper, 0.0])
        )
        densities = self._density_and_derivative(ratio_candidates)[0]
        ratio_values = ratio_candidates * np.sqrt(densities)
        v_min = np.nextafter(np.min(ratio_values), -np.inf)
        v_max = np.nextafter(np.max(ratio_values), np.inf)
        return float(u_max), float(v_min), float(v_max)

    def plot_acceptance_region(
        self,
        candidate_points: np.ndarray | None = None,
        grid_size: int = 1500,
        ax=None,
        show: bool = False,
    ):
        from .ratio_of_uniforms_visualization import plot_acceptance_region

        return plot_acceptance_region(
            self,
            candidate_points=candidate_points,
            grid_size=grid_size,
            ax=ax,
            show=show,
        )

    def plot_mixture_density(
        self,
        x_limits: tuple[float, float] | None = None,
        grid_size: int = 1200,
        ax=None,
        show: bool = False,
    ):
        from .ratio_of_uniforms_visualization import plot_mixture_density

        return plot_mixture_density(
            self,
            x_limits=x_limits,
            grid_size=grid_size,
            ax=ax,
            show=show,
        )

    def generate(self, n: int, random_state=None) -> np.ndarray:
        if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)):
            raise TypeError("n must be a non-negative integer")
        if n < 0:
            raise ValueError("n must be a non-negative integer")
        if n == 0:
            return np.empty(0, dtype=np.float64)

        rng = np.random.default_rng(random_state)
        samples = []
        accepted_count = 0
        attempts = 0
        attempt_budget = max(100_000, n * 1000)
        batch_limit = 65_536

        while accepted_count < n and attempts < attempt_budget:
            remaining = n - accepted_count
            batch_size = min(batch_limit, max(1024, remaining * 2))
            batch_size = min(batch_size, attempt_budget - attempts)
            u = rng.uniform(0.0, self.u_max, size=batch_size)
            v = rng.uniform(self.v_min, self.v_max, size=batch_size)
            attempts += batch_size

            nonzero_u = u > 0.0
            candidates = np.empty(batch_size, dtype=np.float64)
            candidates.fill(np.nan)
            candidates[nonzero_u] = v[nonzero_u] / u[nonzero_u]
            density = np.zeros(batch_size, dtype=np.float64)
            density[nonzero_u] = self._density_and_derivative(
                candidates[nonzero_u]
            )[0]
            accepted = nonzero_u & (u**2 < density)
            accepted_batch = candidates[accepted]
            samples.append(accepted_batch)
            accepted_count += accepted_batch.size

        if accepted_count < n:
            raise RuntimeError(
                "Ratio-of-Uniforms rejection sampling exceeded its candidate limit"
            )

        return np.concatenate(samples)[:n]
