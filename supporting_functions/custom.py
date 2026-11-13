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

