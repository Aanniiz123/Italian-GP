import pandas as pd
import numpy as np
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_URL = SCRIPT_DIR.parent / "data" / "raw"

# Make sure `backend/` is on sys.path so `config` is importable
# regardless of where this script is run from
sys.path.append(str(SCRIPT_DIR.parent))
from config.logger import get_logger

logger = get_logger(__name__)


def fetch_year_data(year: int) -> pd.DataFrame:
    """
    Load CSV data for a specific year.
    Parameters
    ----------
    year : int
        Year of the data.
    Returns
    -------
    pd.DataFrame
        DataFrame containing the year's data.
    """
    file_path = BASE_URL / str(year) / "race" / "results.csv"

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded data for {year}")
        return df

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error loading {year}: {e}")
        return pd.DataFrame()


def data_information(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw results DataFrame by dropping:
    1. Columns with 20 or more null values.
    2. A fixed set of known-irrelevant columns.
    """
    df = df.copy()

    high_null_cols = df.columns[df.isna().sum() >= 20]
    if len(high_null_cols) > 0:
        logger.info(f"Dropping high-null columns: {list(high_null_cols)}")
        df = df.drop(columns=high_null_cols)

    cols_to_drop = ['HeadshotUrl', 'TeamColor', 'BroadcastName', 'DriverNumber', 'ClassifiedPosition',
                    'TeamId', 'DriverId', 'FirstName', 'LastName', 'CountryCode']
    existing_cols_to_drop = [c for c in cols_to_drop if c in df.columns]

    if existing_cols_to_drop:
        logger.info(f"Dropping fixed columns: {existing_cols_to_drop}")
        df = df.drop(columns=existing_cols_to_drop)

    return df


def data_merge(data: dict) -> pd.DataFrame:
    """
    Merge multiple years of cleaned race data into a single DataFrame.
    """
    frames = []

    for year, df in data.items():
        if df.empty:
            logger.warning(f"Skipping {year} — empty DataFrame")
            continue

        df = df.copy()
        df['Year'] = year
        frames.append(df)

    if not frames:
        logger.error("No data available to merge — all years empty")
        return pd.DataFrame()

    merged_df = pd.concat(frames, ignore_index=True)
    logger.info(f"Merged {len(frames)} years into shape {merged_df.shape}")

    return merged_df


def data_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Time / gap to leader ---
    df['Time'] = pd.to_timedelta(df['Time'], errors='coerce')
    df['diff_seconds'] = df['Time'].dt.total_seconds()
    df.loc[df['Position'] == 1, 'diff_seconds'] = 0
    df = df.drop(columns=['Time'], errors='ignore')

    # --- Position / GridPosition validation ---
    df['Position'] = pd.to_numeric(df['Position'], errors='coerce')
    df['GridPosition'] = pd.to_numeric(df['GridPosition'], errors='coerce')

    invalid_pos = (df['Position'] < 0) | (df['GridPosition'] < 0)
    if invalid_pos.any():
        logger.warning(f"Found {invalid_pos.sum()} rows with negative Position/GridPosition — setting to NaN")
        df.loc[df['Position'] < 0, 'Position'] = np.nan
        df.loc[df['GridPosition'] < 0, 'GridPosition'] = np.nan

    # --- Position change (grid vs finish) — always positive magnitude ---
    df['position_change'] = (df['GridPosition'] - df['Position']).abs()

    # --- DNF flag ---
    if 'Laps' in df.columns:
        laps_per_race = df.groupby(['Year'])['Laps'].transform('max')
        df['dnf'] = (df['Laps'] != laps_per_race).astype(int)

    return df


def save_data(df: pd.DataFrame, filename: str = "clean_results.csv") -> None:
    """
    Save the cleaned/merged DataFrame to the processed data directory.
    """
    if df.empty:
        logger.warning("Attempted to save an empty DataFrame — skipping save.")
        return

    output_dir = SCRIPT_DIR.parent / "data" / "processed"

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path} (shape={df.shape})")

    except Exception as e:
        logger.error(f"Error saving data to {output_dir / filename}: {e}")

def main():
    years = range(2020, 2026)

    data = {}
    logger.info("Starting data fetching...")

    for year in years:
        logger.info(f"Fetching data for {year}")
        data[year] = fetch_year_data(year)

    cleaned_data = {}
    logger.info("Starting data cleaning...")

    for year in years:
        if not data[year].empty:
            logger.info(f"Cleaning data for {year}")
            cleaned_data[year] = data_information(data[year])
        else:
            logger.warning(f"Skipping {year} — no data loaded")
            cleaned_data[year] = pd.DataFrame()

    logger.info("Merging all years...")
    merged_df = data_merge(cleaned_data)

    if merged_df.empty:
        logger.error("No data available after merging.")
        return

    logger.info("=" * 50)
    logger.info("FINAL DATASET INFORMATION")
    logger.info("=" * 50)
    logger.info(f"Shape: {merged_df.shape}")
    logger.info(f"Columns: {merged_df.columns.tolist()}")
    logger.info(f"First 5 rows:\n{merged_df.head()}")
    logger.info(f"Missing values:\n{merged_df.isna().sum()}")
    logger.info(f"Data types:\n{merged_df.dtypes}")

    logger.info("Running data_clean (time diff, position change, dnf)...")
    clean_df = data_clean(merged_df)

    logger.info("=" * 50)
    logger.info("CLEANED DATASET")
    logger.info("=" * 50)
    logger.info(f"Columns: {clean_df.columns.tolist()}")
    logger.info(f"First 5 rows:\n{clean_df.head(5)}")

    logger.info("Saving cleaned data...")
    save_data(clean_df)

    return clean_df


if __name__ == "__main__":
    df = main()