import json
import pandas as pd
from pathlib import Path
import re

# ---------------------------
# Setup: Load Files and Data
# ---------------------------
# Define the base path for the patents data and where the filtered data will be saved.
BASE_PATH = Path("data/patents")
csv_path = BASE_PATH / "merged_df.csv"
FILTERED_PATH = Path("data/filtered")

# Load the original DataFrame from a CSV file.
# The CSV file contains all the raw data we need to filter.
dataframe_original = pd.read_csv(csv_path, low_memory=False)

# Load the JSON file that contains configuration data.
# This file holds settings like the list of desired compounds.
json_path = Path("json/properties.json")
with open(json_path, 'r') as file:
    data = json.load(file)

# ---------------------------
# Function Definitions
# ---------------------------

def filter_by_compounds(dataframe):
    """
    Filters columns based on a predefined list of desired compounds.
    It keeps only the columns whose names appear in the desired compounds list.
    
    Returns:
    - A DataFrame containing only the desired compound columns.
    - A DataFrame with the columns that were excluded.
    """
    # Get the list of desired compounds from the JSON data.
    desired_compounds = data["desired_compounds"]
    # Create a list of columns that match the desired compounds.
    filtered_columns = [col for col in dataframe.columns if col in desired_compounds]
    # Identify columns that are not in the desired compounds list.
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

def filter_columns_without_plus(dataframe):
    """
    Filters columns based on whether their names contain the '+' character.
    This is useful when you want to exclude columns with special characters.
    
    Returns:
    - A DataFrame with columns that do NOT contain the '+' character.
    - A DataFrame with columns that DO contain the '+' character.
    """
    # Keep columns without '+' in their names.
    filtered_columns = [col for col in dataframe.columns if "+" not in col]
    # Identify columns that contain '+'.
    excluded_columns = [col for col in dataframe.columns if "+" in col]
    return dataframe[filtered_columns], dataframe[excluded_columns]

def clean_and_fill_zeros(dataframe):
    """
    Cleans the DataFrame by:
    - Replacing the string '—' with 0.
    - Filling any NaN (missing) values with 0.
    - Converting all columns to numeric values.
    
    This ensures that the DataFrame can be safely used for mathematical operations.
    """
    # Replace '—' with 0 and fill missing values.
    dataframe = dataframe.replace('—', 0).fillna(0)
    # Convert all values to numeric, coercing errors to NaN and then replacing them with 0.
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

def remove_columns_with_only_zeros(dataframe):
    """
    Removes columns that contain only zeros since they don't provide useful information.
    
    Returns:
    - A DataFrame without the columns that are completely 0.
    - A DataFrame of the columns that were removed (all zeros).
    """
    # Identify columns where every entry is 0.
    empty_columns = dataframe.columns[(dataframe == 0).all()]
    excluded_columns_df = dataframe[empty_columns]
    # Drop those columns from the original DataFrame.
    filtered_dataframe = dataframe.drop(columns=empty_columns)
    return filtered_dataframe, excluded_columns_df

def filter_rows_by_sum(dataframe, tolerance=2):
    """
    Filters rows based on the sum of their values.
    The function keeps rows that sum to approximately 100,
    or rows that sum to approximately 1 (which are then scaled to 100).
    
    Returns:
    - A DataFrame with rows that have sums approximately equal to 100.
    - A DataFrame with rows that were excluded.
    """
    # Calculate the sum of each row.
    row_sums = dataframe.sum(axis=1)
    tolerance_100 = tolerance      # Tolerance for sums around 100.
    tolerance_1 = tolerance / 100  # Tolerance for sums around 1 (to be scaled).

    # Create masks for rows that sum near 100 or near 1.
    mask_sum_100 = (row_sums >= 100 - tolerance_100) & (row_sums <= 100 + tolerance_100)
    mask_sum_1 = (row_sums >= 1 - tolerance_1) & (row_sums <= 1 + tolerance_1)

    # Extract rows with sums near 100.
    rows_sum_100 = dataframe.loc[mask_sum_100]
    # Extract rows with sums near 1 and scale them up by multiplying by 100.
    rows_sum_1_scaled = dataframe.loc[mask_sum_1] * 100

    # Combine both groups of rows.
    combined_rows = pd.concat([rows_sum_100, rows_sum_1_scaled])
    # The excluded rows are those that do not meet either criterion.
    excluded_rows = dataframe.drop(combined_rows.index)

    return combined_rows, excluded_rows

def filter_columns_by_properties(dataframe):
    """
    Filters columns based on a predefined list of property keywords.
    Only columns whose names contain one of the keywords will be kept.
    
    Returns:
    - A DataFrame with columns that match the property keywords.
    - A DataFrame with columns that do not match.
    """
    # List of keywords related to material properties.
    properties = ["refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", 
                  "devitrification", "point", "crystallization", "thermal", "mean", 
                  "glass transition", "crystallinity", "electric", "onset", "transition", 
                  "permittivity", "iso", "RI", "index", "ref", "nd", "η", "nm", "ratio", 
                  "n5", "n6", "n7", "n8", "n9"]
    # Select columns that contain any of the keywords (case-insensitive check).
    filtered_columns = [col for col in dataframe.columns if any(prop.lower() in col.lower() for prop in properties)]
    filtered_dataframe = dataframe[filtered_columns]
    # The rest of the 
