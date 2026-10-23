import pandas as pd
from pathlib import Path


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Drop selected columns and rows with at least two missing values."""
    columns_to_drop = [
        "Unnamed: 0",
        "exp_molecular_weight",
        "exp_pka",
        "exp_logp",
        "half_life",
    ]
    df = (
        df.drop(columns=columns_to_drop)
        .replace(r"^\s*$", pd.NA, regex=True)
        .copy()
    )
    df["cal_water_solubility"] = pd.to_numeric(
        df["cal_water_solubility"].str.replace(
            r"\s*g/l\s*$", "", regex=True, case=False
        ),
        errors="raise",
    )
    rows_to_keep = df.isna().sum(axis=1) < 2
    return df.loc[rows_to_keep].reset_index(drop=True)


def clean_data(data_path: str | Path | None = None) -> pd.DataFrame:
    """Load and clean DrugBank data."""
    if data_path is None:
        data_path = Path(__file__).resolve().parents[1] / "drugbank.csv"
    return clean_dataframe(pd.read_csv(data_path))


def save_cleaned_data(
    df: pd.DataFrame,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Clean a dataframe, save it to CSV, and return the cleaned dataframe."""
    if output_path is None:
        output_path = Path(__file__).resolve().parents[1] / "cleaned_data.csv"

    cleaned_df = clean_dataframe(df)
    cleaned_df.to_csv(output_path, index=False)
    return cleaned_df


def preview_cleaning(data_path: str | Path | None = None) -> None:
    """Print the number of rows removed by cleaning the dataset."""
    if data_path is None:
        data_path = Path(__file__).resolve().parents[1] / "drugbank.csv"

    original_df = pd.read_csv(data_path)
    cleaned_df = clean_dataframe(original_df)
    print(len(original_df) - len(cleaned_df))


if __name__ == "__main__":
    source_path = Path(__file__).resolve().parents[1] / "drugbank.csv"
    original_df = pd.read_csv(source_path)
    cleaned_df = save_cleaned_data(original_df)
    print(f"Saved {len(cleaned_df)} rows to cleaned_data.csv")