import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def _validate_grid_size(grid_size: int) -> None:
    if isinstance(grid_size, (bool, np.bool_)) or not isinstance(
        grid_size, (int, np.integer)
    ):
        raise TypeError("grid_size must be an integer")
    if grid_size < 2:
        raise ValueError("grid_size must be at least 2")


def _density_grid(generator, grid_size: int) -> np.ndarray:
    means = generator.means
    standard_deviations = generator._standard_deviations
    lower = float(np.min(means - 8.0 * standard_deviations))
    upper = float(np.max(means + 8.0 * standard_deviations))
    grid_parts = [np.linspace(lower, upper, grid_size)]
    local_size = max(128, grid_size // 6)
    for mean, standard_deviation in zip(means, standard_deviations):
        grid_parts.append(
            np.linspace(
                mean - 8.0 * standard_deviation,
                mean + 8.0 * standard_deviation,
                local_size,
            )
        )
    return np.unique(np.concatenate(grid_parts))


def plot_acceptance_region(
    generator,
    candidate_points: np.ndarray | None = None,
    grid_size: int = 1500,
    ax=None,
    show: bool = False,
):
    """Plot the Ratio-of-Uniforms acceptance region and its bounding rectangle.

    ``candidate_points``, when supplied, must be an ``(n, 2)`` array with
    columns ``(U, V)``; points are colored according to the acceptance test.
    """
    _validate_grid_size(grid_size)
    if candidate_points is not None:
        candidate_points = np.asarray(candidate_points, dtype=np.float64)
        if candidate_points.ndim != 2 or candidate_points.shape[1] != 2:
            raise ValueError("candidate_points must have shape (n, 2)")
        if not np.all(np.isfinite(candidate_points)):
            raise ValueError("candidate_points must contain only finite values")

    x = _density_grid(generator, grid_size)
    density = generator._density_and_derivative(x)[0]
    boundary_u = np.sqrt(density)
    boundary_v = x * boundary_u

    if ax is None:
        figure, ax = plt.subplots(figsize=(9, 6))
    else:
        figure = ax.figure

    region_u = np.concatenate(([0.0], boundary_u, [0.0]))
    region_v = np.concatenate(([0.0], boundary_v, [0.0]))
    ax.fill(
        region_u,
        region_v,
        color="tab:blue",
        alpha=0.25,
        label="Acceptance region",
    )
    rectangle = Rectangle(
        (0.0, generator.v_min),
        generator.u_max,
        generator.v_max - generator.v_min,
        fill=False,
        edgecolor="black",
        linewidth=1.5,
        linestyle="--",
        label="Bounding rectangle",
    )
    ax.add_patch(rectangle)
    ax.axvline(
        generator.u_max,
        color="tab:purple",
        linestyle=":",
        label=r"$u_{\max}$",
    )
    ax.axhline(
        generator.v_min,
        color="tab:green",
        linestyle=":",
        label=r"$v_{\min}$",
    )
    ax.axhline(
        generator.v_max,
        color="tab:orange",
        linestyle=":",
        label=r"$v_{\max}$",
    )

    if candidate_points is not None and candidate_points.size:
        candidate_u = candidate_points[:, 0]
        candidate_v = candidate_points[:, 1]
        positive_u = candidate_u > 0.0
        candidate_x = np.zeros(candidate_u.shape, dtype=np.float64)
        candidate_x[positive_u] = (
            candidate_v[positive_u] / candidate_u[positive_u]
        )
        candidate_density = np.zeros(candidate_u.shape, dtype=np.float64)
        candidate_density[positive_u] = generator._density_and_derivative(
            candidate_x[positive_u]
        )[0]
        accepted = positive_u & (candidate_u**2 < candidate_density)
        ax.scatter(
            candidate_u[accepted],
            candidate_v[accepted],
            s=18,
            color="tab:green",
            label="Accepted candidates",
            zorder=3,
        )
        ax.scatter(
            candidate_u[~accepted],
            candidate_v[~accepted],
            s=18,
            color="tab:red",
            label="Rejected candidates",
            zorder=3,
        )

    ax.set_xlabel("U")
    ax.set_ylabel("V")
    ax.set_title("Ratio-of-Uniforms acceptance region")
    ax.legend()
    figure.tight_layout()
    if show:
        plt.show()
    return figure, ax


def plot_mixture_density(
    generator,
    x_limits: tuple[float, float] | None = None,
    grid_size: int = 1200,
    ax=None,
    show: bool = False,
):
    """Plot the fitted Gaussian components and their mixture density."""
    _validate_grid_size(grid_size)
    if x_limits is None:
        x = _density_grid(generator, grid_size)
    else:
        if (
            len(x_limits) != 2
            or not np.all(np.isfinite(x_limits))
            or x_limits[0] >= x_limits[1]
        ):
            raise ValueError("x_limits must contain two increasing finite values")
        x = np.linspace(x_limits[0], x_limits[1], grid_size)

    offsets = x[:, None] - generator.means[None, :]
    component_densities = (
        generator.weights[None, :]
        * np.exp(-0.5 * offsets**2 / generator.variances[None, :])
        / np.sqrt(2.0 * np.pi * generator.variances[None, :])
    )
    mixture_density = np.sum(component_densities, axis=1)

    if ax is None:
        figure, ax = plt.subplots(figsize=(9, 5))
    else:
        figure = ax.figure

    for component_index in range(generator.weights.size):
        ax.plot(
            x,
            component_densities[:, component_index],
            linestyle="--",
            label=f"Component {component_index + 1}",
        )
    ax.plot(
        x,
        mixture_density,
        color="black",
        linewidth=2,
        label="Three-component mixture",
    )
    ax.set_xlabel("x")
    ax.set_ylabel("Density")
    ax.set_title("Fitted Gaussian mixture density")
    ax.legend()
    figure.tight_layout()
    if show:
        plt.show()
    return figure, ax
