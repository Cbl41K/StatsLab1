import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def gaussian_kernel(u):
    """Evaluate the standard normal density at ``u``."""
    u = np.asarray(u, dtype=np.float64)
    return np.exp(-0.5 * u**2) / np.sqrt(2.0 * np.pi)


def kde(data, x, h, kernel=gaussian_kernel, chunk_size=256):
    """Estimate density using any vectorized kernel callable ``kernel``."""
    data = np.asarray(data, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)

    if h <= 0:
        raise ValueError("h must be positive")
    data = data[np.isfinite(data)]
    if data.size == 0:
        raise ValueError("data contains no finite values")

    result = np.empty(x.size, dtype=np.float64)
    for start in range(0, x.size, chunk_size):
        stop = min(start + chunk_size, x.size)
        u = (x[start:stop, None] - data[None, :]) / h
        result[start:stop] = np.asarray(kernel(u)).mean(axis=1) / h

    return result


def find_prominent_peaks(density, relative_prominence=0.01):
    """Return local-maximum indices with prominence above a relative threshold."""
    density = np.asarray(density, dtype=np.float64)
    if density.ndim != 1 or density.size < 3:
        raise ValueError("density must be a one-dimensional array with at least 3 values")
    if not np.all(np.isfinite(density)):
        raise ValueError("density must contain only finite values")
    if relative_prominence < 0:
        raise ValueError("relative_prominence must be non-negative")

    candidates = np.flatnonzero(
        (density[1:-1] > density[:-2]) & (density[1:-1] > density[2:])
    ) + 1
    min_prominence = relative_prominence * density.max()
    prominent = []

    for peak in candidates:
        left = peak
        while left > 0 and density[left - 1] <= density[peak]:
            left -= 1
        right = peak
        while right < density.size - 1 and density[right + 1] <= density[peak]:
            right += 1

        left_base = density[left:peak + 1].min()
        right_base = density[peak:right + 1].min()
        prominence = density[peak] - max(left_base, right_base)
        if prominence >= min_prominence:
            prominent.append(peak)

    return np.asarray(prominent, dtype=int)


def plot_kde(data, h, kernel=gaussian_kernel, gridsize=500, ax=None):
    """Plot a KDE using any vectorized kernel callable ``kernel``."""
    data = np.asarray(data, dtype=np.float64)
    data = data[np.isfinite(data)]
    if data.size == 0:
        raise ValueError("data contains no finite values")

    x_grid = np.linspace(data.min(), data.max(), gridsize)
    density = kde(data, x_grid, h=h, kernel=kernel)

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))

    ax.plot(x_grid, density)
    ax.set_xlabel("cal_pka_basic")
    ax.set_ylabel("Density")
    ax.set_title("Kernel Density Estimate")
    return ax


def summarize_kde_groups(data):
    """Return KDE cut points and group statistics for bandwidths 0.60 to 1.00."""
    values = np.asarray(data, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("data must be one-dimensional")
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError("data contains no finite values")

    h_values = np.round(np.arange(0.60, 1.001, 0.05), 2)
    rows = []
    for h in h_values:
        x_grid = np.linspace(values.min() - 3 * h, values.max() + 3 * h, 1000)
        density = kde(values, x_grid, h=h)
        peak_indices = find_prominent_peaks(density)
        if peak_indices.size < 3:
            raise ValueError(
                f"Expected at least 3 prominent KDE peaks for h={h:.2f}; "
                f"found {peak_indices.size}"
            )

        first_three_peaks = peak_indices[:3]
        first_minimum = first_three_peaks[0] + np.argmin(
            density[first_three_peaks[0] : first_three_peaks[1] + 1]
        )
        second_minimum = first_three_peaks[1] + np.argmin(
            density[first_three_peaks[1] : first_three_peaks[2] + 1]
        )
        b_1 = x_grid[first_minimum]
        b_2 = x_grid[second_minimum]
        groups = (
            values[values <= b_1],
            values[(values > b_1) & (values <= b_2)],
            values[values > b_2],
        )

        row = {"h": h, "b_1(h)": b_1, "b_2(h)": b_2}
        for index, group in enumerate(groups, start=1):
            row[f"number_{index}"] = group.size
            row[f"expected_value_{index}"] = group.mean() if group.size else np.nan
            row[f"variance_{index}"] = (
                group.var(ddof=1) if group.size > 1 else np.nan
            )
        rows.append(row)

    return pd.DataFrame(rows)


def plot_normal_mixture_comparison(data, summary, h_values=(0.6, 0.8, 1.0), ax=None):
    """Compare the empirical data KDE with normal mixtures from KDE group summaries."""
    values = np.asarray(data, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("data must be one-dimensional")
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError("data contains no finite values")

    required_columns = {"h"}
    for component in range(1, 4):
        required_columns.update(
            {
                f"number_{component}",
                f"expected_value_{component}",
                f"variance_{component}",
            }
        )
    missing_columns = required_columns.difference(summary.columns)
    if missing_columns:
        raise ValueError(f"summary is missing columns: {sorted(missing_columns)}")

    models = []
    for h in h_values:
        matches = summary[np.isclose(summary["h"], h)]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one summary row for h={h}")
        row = matches.iloc[0]
        means = np.asarray(
            [row[f"expected_value_{i}"] for i in range(1, 4)], dtype=np.float64
        )
        variances = np.asarray(
            [row[f"variance_{i}"] for i in range(1, 4)], dtype=np.float64
        )
        counts = np.asarray(
            [row[f"number_{i}"] for i in range(1, 4)], dtype=np.float64
        )
        if (
            not np.all(np.isfinite(means))
            or not np.all(np.isfinite(variances))
            or not np.all(np.isfinite(counts))
            or np.any(variances <= 0)
            or np.any(counts <= 0)
        ):
            raise ValueError(
                f"summary values for h={h} must be finite; variances and counts "
                "must be positive"
            )
        models.append((h, means, variances, counts / counts.sum()))

    max_sigma = max(np.sqrt(variances).max() for _, _, variances, _ in models)
    means = np.concatenate([model_means for _, model_means, _, _ in models])
    x_min = min(values.min(), (means - 4 * max_sigma).min())
    x_max = max(values.max(), (means + 4 * max_sigma).max())
    x_grid = np.linspace(x_min, x_max, 700)

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        x_grid,
        kde(values, x_grid, h=0.8),
        color="black",
        linewidth=2,
        label="Original data KDE (h=0.8)",
    )
    colors = ("tab:blue", "tab:orange", "tab:green")
    for (h, component_means, variances, weights), color in zip(models, colors):
        standard_deviations = np.sqrt(variances)
        component_densities = (
            np.exp(
                -0.5
                * ((x_grid[:, None] - component_means) / standard_deviations) ** 2
            )
            / (standard_deviations * np.sqrt(2.0 * np.pi))
        )
        mixture_density = component_densities @ weights
        ax.plot(
            x_grid,
            mixture_density,
            color=color,
            label=f"Normal mixture (h={h:g})",
        )
        for mean in component_means:
            ax.axvline(mean, color=color, linestyle=":", linewidth=1, alpha=0.4)

    ax.set_xlabel("cal_pka_basic")
    ax.set_ylabel("Density")
    ax.set_title("Original data and three-component normal mixtures")
    ax.legend()
    ax.grid(alpha=0.2)
    return ax


def _run_probabilities_opt(
    data,
    initial_cons,
    max_iterations,
    tolerance=None,
    consecutive_iterations=5,
):
    """Run fixed-step or convergence-based EM and return per-observation history."""
    values = np.asarray(data, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("data must be one-dimensional")
    finite_mask = np.isfinite(values)
    observation_indices = np.flatnonzero(finite_mask)
    values = values[finite_mask]
    if values.size == 0:
        raise ValueError("data contains no finite values")
    if (
        isinstance(max_iterations, (bool, np.bool_))
        or not isinstance(max_iterations, (int, np.integer))
        or max_iterations < 0
    ):
        raise ValueError("max_iterations must be a non-negative integer")
    if tolerance is not None and (not np.isfinite(tolerance) or tolerance <= 0):
        raise ValueError("tolerance must be finite and positive")
    if (
        isinstance(consecutive_iterations, (bool, np.bool_))
        or not isinstance(consecutive_iterations, (int, np.integer))
        or consecutive_iterations < 1
    ):
        raise ValueError("consecutive_iterations must be a positive integer")

    if isinstance(initial_cons, pd.DataFrame):
        if len(initial_cons) != 1:
            raise ValueError("initial_cons DataFrame must contain exactly one row")
        initial_cons = initial_cons.iloc[0]
    if not isinstance(initial_cons, (pd.Series, dict)):
        raise TypeError("initial_cons must be a one-row DataFrame, Series, or dict")

    means = np.asarray(
        [initial_cons[f"expected_value_{i}"] for i in range(1, 4)],
        dtype=np.float64,
    )
    variances = np.asarray(
        [initial_cons[f"variance_{i}"] for i in range(1, 4)],
        dtype=np.float64,
    )
    counts = np.asarray(
        [initial_cons[f"number_{i}"] for i in range(1, 4)],
        dtype=np.float64,
    )
    if (
        not np.all(np.isfinite(means))
        or not np.all(np.isfinite(variances))
        or not np.all(np.isfinite(counts))
        or np.any(variances <= 0)
        or np.any(counts <= 0)
    ):
        raise ValueError(
            "initial means must be finite; variances and counts must be finite "
            "and positive"
        )
    weights = counts / counts.sum()

    history = []
    previous_log_likelihood = None
    stable_iterations = 0
    converged = False
    for iteration in range(max_iterations + 1):
        log_density = -0.5 * (
            np.log(2.0 * np.pi * variances)[None, :]
            + (values[:, None] - means[None, :]) ** 2 / variances[None, :]
        )
        log_joint = log_density + np.log(weights)[None, :]
        max_log_joint = log_joint.max(axis=1, keepdims=True)
        scaled_joint = np.exp(log_joint - max_log_joint)
        normalizers = scaled_joint.sum(axis=1, keepdims=True)
        probabilities = scaled_joint / normalizers
        log_likelihood = float(
            np.sum(max_log_joint[:, 0] + np.log(normalizers[:, 0]))
        )

        relative_change = np.nan
        if previous_log_likelihood is not None:
            relative_change = abs(log_likelihood - previous_log_likelihood) / (
                1.0 + abs(previous_log_likelihood)
            )
            if tolerance is not None:
                stable_iterations = (
                    stable_iterations + 1 if relative_change < tolerance else 0
                )
                converged = stable_iterations >= consecutive_iterations

        step = pd.DataFrame(
            {
                "iteration": iteration,
                "observation": observation_indices,
                "value": values,
            }
        )
        for component in range(3):
            step[f"probability_{component + 1}"] = probabilities[:, component]
            step[f"weight_{component + 1}"] = weights[component]
            step[f"expected_value_{component + 1}"] = means[component]
            step[f"variance_{component + 1}"] = variances[component]
        if tolerance is not None:
            step["log_likelihood"] = log_likelihood
            step["relative_change"] = relative_change
            step["converged"] = converged
        history.append(step)

        if iteration == max_iterations or converged:
            break

        effective_counts = probabilities.sum(axis=0)
        if np.any(effective_counts <= np.finfo(np.float64).tiny):
            raise ValueError("a component received no posterior probability")
        weights = effective_counts / values.size
        means = (probabilities * values[:, None]).sum(axis=0) / effective_counts
        variances = (
            probabilities * (values[:, None] - means[None, :]) ** 2
        ).sum(axis=0) / effective_counts
        if not np.all(np.isfinite(variances)) or np.any(variances <= 0):
            raise ValueError("optimization produced a non-positive variance")
        previous_log_likelihood = log_likelihood

    return pd.concat(history, ignore_index=True)


def probabilities_opt(data, initial_cons, number_of_iterations):
    """Run a fixed number of EM updates and return per-observation history."""
    return _run_probabilities_opt(data, initial_cons, number_of_iterations)


def probabilities_opt_until_convergence(
    data,
    initial_cons,
    tolerance=1e-6,
    consecutive_iterations=5,
    max_iterations=1000,
):
    """Run EM until relative log-likelihood change is small for several steps."""
    return _run_probabilities_opt(
        data,
        initial_cons,
        max_iterations,
        tolerance=tolerance,
        consecutive_iterations=consecutive_iterations,
    )


def integrated_squared_error(x, reference_density, model_density):
    """Numerically integrate the squared difference between two density curves."""
    x = np.asarray(x, dtype=np.float64)
    reference_density = np.asarray(reference_density, dtype=np.float64)
    model_density = np.asarray(model_density, dtype=np.float64)
    if (
        x.ndim != 1
        or reference_density.ndim != 1
        or model_density.ndim != 1
        or x.size < 2
        or reference_density.size != x.size
        or model_density.size != x.size
    ):
        raise ValueError("x and both densities must be one-dimensional and equal-sized")
    if (
        not np.all(np.isfinite(x))
        or not np.all(np.isfinite(reference_density))
        or not np.all(np.isfinite(model_density))
    ):
        raise ValueError("x and both densities must contain only finite values")
    intervals = np.diff(x)
    if np.any(intervals <= 0):
        raise ValueError("x must be strictly increasing")

    squared_error = (reference_density - model_density) ** 2
    return float(
        np.sum(0.5 * (squared_error[:-1] + squared_error[1:]) * intervals)
    )

