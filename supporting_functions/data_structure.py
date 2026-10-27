import math

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _numeric_plot_layout(
    df: pd.DataFrame,
    plot_name: str,
) -> tuple[pd.Index, plt.Figure, object]:
    columns = df.select_dtypes(include="number").columns
    if len(columns) == 0:
        raise ValueError("The dataframe contains no numeric columns to plot.")

    columns_per_row = min(3, len(columns))
    rows = math.ceil(len(columns) / columns_per_row)
    figure, axes = plt.subplots(
        rows,
        columns_per_row,
        figsize=(5 * columns_per_row, 4 * rows),
        squeeze=False,
    )
    figure.suptitle(plot_name, y=0.99)
    return columns, figure, axes


def numericReview(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize missingness, uniqueness, and numeric statistics by column."""
    normalized = df.replace(r"^\s*$", pd.NA, regex=True)
    summary = pd.DataFrame(
        {
            "dtype": [str(df[column].dtype) for column in df.columns],
            "spaces": normalized.isna().sum(),
            "number of unique values": normalized.nunique(dropna=True),
            "mean_value": pd.NA,
            "median_value": pd.NA,
            "std": pd.NA,
            "iqr": pd.NA,
        },
        index=df.columns,
    )

    for column in df.select_dtypes(include="number").columns:
        values = normalized[column].dropna()
        summary.loc[column, "mean_value"] = values.mean()
        summary.loc[column, "median_value"] = values.median()
        summary.loc[column, "std"] = values.std()
        summary.loc[column, "iqr"] = values.quantile(0.75) - values.quantile(0.25)

    summary.index.name = "column_name"
    return summary


def plot_histograms(df: pd.DataFrame) -> tuple[plt.Figure, object]:
    """Build a Seaborn histogram for each numeric dataframe column."""
    columns, figure, axes = _numeric_plot_layout(df, "Numeric column histograms")
    colors = sns.color_palette("husl", n_colors=len(columns))
    for axis, column, color in zip(axes.flat, columns, colors):
        values = df[column].dropna()
        if values.empty:
            axis.text(0.5, 0.5, "No data", ha="center", va="center")
        else:
            sns.histplot(x=values, color=color, ax=axis)
        #axis.set_title(str(column))

    for axis in axes.flat[len(columns) :]:
        axis.set_visible(False)
    figure.tight_layout(rect=[0, 0, 1, 0.99])
    return figure, axes


def plot_kdes(df: pd.DataFrame) -> tuple[plt.Figure, object]:
    """Build a Seaborn KDE plot for each numeric dataframe column."""
    columns, figure, axes = _numeric_plot_layout(df, "Numeric column KDE plots")
    colors = sns.color_palette("husl", n_colors=len(columns))
    for axis, column, color in zip(axes.flat, columns, colors):
        values = df[column].dropna()
        if values.nunique() < 2:
            axis.text(
                0.5,
                0.5,
                "KDE requires at least two distinct values",
                ha="center",
                va="center",
            )
        else:
            sns.kdeplot(x=values, color=color, ax=axis)
        #axis.set_title(str(column))

    for axis in axes.flat[len(columns) :]:
        axis.set_visible(False)
    figure.tight_layout(rect=[0, 0, 1, 0.99])
    return figure, axes


def plot_boxplots(df: pd.DataFrame) -> tuple[plt.Figure, object]:
    """Build a Seaborn boxplot for each numeric dataframe column."""
    columns, figure, axes = _numeric_plot_layout(df, "Numeric column boxplots")
    colors = sns.color_palette("husl", n_colors=len(columns))
    for axis, column, color in zip(axes.flat, columns, colors):
        values = df[column].dropna()
        if values.empty:
            axis.text(0.5, 0.5, "No data", ha="center", va="center")
        else:
            sns.boxplot(x=values, color=color, ax=axis)
        #axis.set_title(str(column))

    for axis in axes.flat[len(columns) :]:
        axis.set_visible(False)
    figure.tight_layout(rect=[0, 0, 1, 0.99])
    return figure, axes


def plot_corr_matrix(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, plt.Figure, plt.Axes]:
    """Plot and return the correlation matrix for numeric dataframe columns."""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        raise ValueError("The dataframe contains no numeric columns to correlate.")

    corr_matrix = numeric_df.corr()
    figure, axis = plt.subplots(
        figsize=(max(6, len(corr_matrix.columns)), max(5, len(corr_matrix) * 0.8))
    )
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap="coolwarm",
        center=0,
        vmin=-1,
        vmax=1,
        fmt=".2f",
        ax=axis,
    )
    axis.set_title("Numeric parameter correlation matrix")
    figure.tight_layout(rect=[0, 0, 1, 0.98])
    return corr_matrix, figure, axis