import numpy as np
import pandas as pd


def final_review(real_data, gen_data_1, gen_data_2):
    """Compare descriptive statistics for real and generated samples.

    Args:
        real_data: Non-empty one-dimensional numeric reference array.
        gen_data_1: Non-empty one-dimensional numeric array from generator 1.
        gen_data_2: Non-empty one-dimensional numeric array from generator 2.

    Returns:
        A DataFrame with the statistics, signed deltas, and relative deviations.
    """
    def validate_array(data, name):
        values = np.asarray(data)
        if values.ndim != 1 or values.size == 0:
            raise ValueError(f"{name} must be a non-empty one-dimensional array.")
        if not np.issubdtype(values.dtype, np.number) or np.issubdtype(
            values.dtype, np.complexfloating
        ):
            raise TypeError(f"{name} must contain real numeric values.")
        return values

    def calculate_statistics(values):
        quartiles = np.percentile(values, [25, 75])
        series = pd.Series(values)
        return {
            "Mean": np.mean(values),
            "Median": np.median(values),
            "Std": np.std(values, ddof=1),
            "Variance": np.var(values, ddof=1),
            "Q25": quartiles[0],
            "Q75": quartiles[1],
            "IQR": quartiles[1] - quartiles[0],
            "Skewness": series.skew(),
            "Kurtosis": series.kurt(),
        }

    def calculate_deviation(generated_value, real_value):
        if np.isclose(real_value, 0):
            return np.nan
        return abs(generated_value - real_value) / abs(real_value) * 100

    real_values = validate_array(real_data, "real_data")
    gen_values_1 = validate_array(gen_data_1, "gen_data_1")
    gen_values_2 = validate_array(gen_data_2, "gen_data_2")

    real_statistics = calculate_statistics(real_values)
    gen_statistics_1 = calculate_statistics(gen_values_1)
    gen_statistics_2 = calculate_statistics(gen_values_2)

    rows = []
    for characteristic, real_value in real_statistics.items():
        gen_value_1 = gen_statistics_1[characteristic]
        gen_value_2 = gen_statistics_2[characteristic]
        rows.append(
            {
                "Characteristic": characteristic,
                "Real data": real_value,
                "Generator 1": gen_value_1,
                "Delta 1": gen_value_1 - real_value,
                "Deviation 1 (%)": calculate_deviation(gen_value_1, real_value),
                "Generator 2": gen_value_2,
                "Delta 2": gen_value_2 - real_value,
                "Deviation 2 (%)": calculate_deviation(gen_value_2, real_value),
            }
        )

    columns = [
        "Characteristic",
        "Real data",
        "Generator 1",
        "Delta 1",
        "Deviation 1 (%)",
        "Generator 2",
        "Delta 2",
        "Deviation 2 (%)",
    ]
    return pd.DataFrame(rows, columns=columns)