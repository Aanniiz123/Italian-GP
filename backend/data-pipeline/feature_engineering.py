import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

# Resolve paths relative to this script's location, not the current working directory.
# Script lives at: monza/backend/data-pipeline/feature_engineering.py
# Data lives at:    monza/backend/data/raw
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_URL = SCRIPT_DIR.parent / "data" / "raw"


def fetch_year_data(year : int) -> pd.DataFrame:
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
        logging.info(f"Successfully loaded data for {year}")
        return df

    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return pd.DataFrame()

    except Exception as e:
        logging.error(f"Error loading {year}: {e}")
        return pd.DataFrame()

def data_information(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw results DataFrame by dropping:
    1. Columns with 20 or more null values.
    2. A fixed set of known-irrelevant columns.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame to clean.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame.
    """
    df = df.copy()

    # 1. Drop columns with >= 20 null values
    high_null_cols = df.columns[df.isna().sum() >= 20]
    if len(high_null_cols) > 0:
        logging.info(f"Dropping high-null columns: {list(high_null_cols)}")
        df = df.drop(columns=high_null_cols)


    # 2. Dropping the irrelevant columns 
    cols_to_drop = ['HeadshotUrl', 'TeamColor', 'BroadcastName','DriverNumber', 'ClassifiedPosition',
                     'DriverId', 'FirstName', 'LastName' , 'CountryCode']
    existing_cols_to_drop = [c for c in cols_to_drop if c in df.columns]
    
    if existing_cols_to_drop:
        logging.info(f"Dropping fixed columns: {existing_cols_to_drop}")
        df = df.drop(columns=existing_cols_to_drop)

    return df

def data_merge(data: dict) -> pd.DataFrame:
    """
    Merge multiple years of cleaned race data into a single DataFrame.

    Parameters
    ----------
    data : dict
        Dictionary of {year: pd.DataFrame}, e.g. the output of cleaning
        each year's data individually.
    Returns
    -------
    pd.DataFrame
        Single concatenated DataFrame containing all years, with a
        'Year' column added to identify the source year of each row.
    """
    frames = []

    for year, df in data.items():
        if df.empty:
            logging.warning(f"Skipping {year} — empty DataFrame")
            continue

        df = df.copy()
        df['Year'] = year
        frames.append(df)

    if not frames:
        logging.error("No data available to merge — all years empty")
        return pd.DataFrame()

    merged_df = pd.concat(frames, ignore_index=True)
    logging.info(f"Merged {len(frames)} years into shape {merged_df.shape}")

    return merged_df


def data_clean(df: pd.DataFrame) -> pd.DataFrame:
    return




def main():
    # Years
    years = range(2020, 2026)

    # Store raw data for each year
    data = {}
    logging.info("Starting data fetching...")
    
    # Fetch data for each year
    for year in years:
        logging.info(f"Fetching data for {year}")
        data[year] = fetch_year_data(year)

    # Store cleaned data
    cleaned_data = {}
    logging.info("Starting data cleaning...")

    # Clean data for each year
    for year in years:
        if not data[year].empty:
            logging.info(f"Cleaning data for {year}")
            cleaned_data[year] = data_information(data[year])
        else:
            logging.warning(f"Skipping {year} — no data loaded")
            cleaned_data[year] = pd.DataFrame()

    # Merge all years
    logging.info("Merging all years...")

    merged_df = data_merge(cleaned_data)

    # Check if merged DataFrame is empty
    if merged_df.empty:
        logging.error("No data available after merging.")
        return

    # Display basic information
    print("\n" + "=" * 50)
    print("FINAL DATASET INFORMATION")
    print("=" * 50)

    print(f"Shape: {merged_df.shape}")

    print("\nColumns:")
    print(merged_df.columns.tolist())

    print("\nFirst 5 rows:")
    print(merged_df.head())

    print("\nMissing values:")
    print(merged_df.isna().sum())

    print("\nData types:")
    print(merged_df.dtypes)

    return merged_df


if __name__ == "__main__":
    df = main()
