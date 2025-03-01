import json
import pandas as pd
from pathlib import Path
import re

# -----------------------------------------------------------------------------
# Function: is_refractive_index_column
# -----------------------------------------------------------------------------
# This function checks if a column name is related to a refractive index.
# It looks for keywords (like 'refrac', 'ref', 'ri', etc.) in the column name.
# If it finds these keywords (and is not confused with 'density'), it returns True.
# Otherwise, it returns False.
def is_refractive_index_column(col_name: str) -> bool:
    lower_name = col_name.lower()  # Convert column name to lowercase for easy comparison
    if 'density' in lower_name:
        return False  # Do not consider columns that contain 'density'
    if "refrac" in lower_name:
        return True
    if re.search(r"ref(\.?)(\s+)?ind", lower_name) or "refr.index" in lower_name:
        return True
    if "ref" in lower_name and "index" in lower_name:
        return True
    if re.search(r"\bri\b", lower_name):
        return True
    if re.search(r"\bnd\b", lower_name, re.IGNORECASE):
        return True
    if re.search(r"\bn\d+(\.\d+)?\b", lower_name):
        return True
    if re.search(r"\bn\s*\(at\s*\d+\s*nm\)", lower_name):
        return True
    if "index" in lower_name and re.search(r"\(@\s*\d+\s*nm\)", lower_name):
        return True
    if re.search(r"ri\s*@", lower_name):
        return True
    return False

# =============================================================================
# Section: Cleaning and Filtering Functions
# =============================================================================

# -----------------------------------------------------------------------------
# Function: clean_and_fill_zeros
# -----------------------------------------------------------------------------
# This function cleans a DataFrame by:
# 1. Replacing any occurrence of the string '—' with the number 0.
# 2. Converting all columns to numeric values (if possible).
# 3. Filling any missing values (NaN) with 0.
def clean_and_fill_zeros(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe.replace('—', 0, inplace=True)
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

# -----------------------------------------------------------------------------
# Function: remove_columns_with_only_zeros
# -----------------------------------------------------------------------------
# This function removes columns that contain only zeros.
# It returns two DataFrames:
# 1. The filtered DataFrame with columns that have at least one non-zero value.
# 2. The DataFrame with columns that were removed (only zeros).
def remove_columns_with_only_zeros(dataframe: pd.DataFrame):
    not_all_zero_mask = (dataframe != 0).any(axis=0)  # True for columns that are not all zeros
    filtered_dataframe = dataframe.loc[:, not_all_zero_mask]
    excluded_columns_df = dataframe.loc[:, ~not_all_zero_mask]
    return filtered_dataframe, excluded_columns_df

# -----------------------------------------------------------------------------
# Function: filter_by_compounds
# -----------------------------------------------------------------------------
# This function keeps only the columns whose names are in the desired compounds list.
# It returns:
# 1. A DataFrame with only the desired compound columns.
# 2. A DataFrame with the columns that were not included.
def filter_by_compounds(dataframe: pd.DataFrame, desired_compounds: list):
    desired_compounds_set = set(desired_compounds)
    filtered_columns_mask = dataframe.columns.isin(desired_compounds_set)
    filtered_df = dataframe.loc[:, filtered_columns_mask]
    excluded_df = dataframe.loc[:, ~filtered_columns_mask]
    return filtered_df, excluded_df

# -----------------------------------------------------------------------------
# Function: filter_rows_by_sum
# -----------------------------------------------------------------------------
# This function keeps only the rows where the sum of values is approximately 100
# or approximately 1 (assuming the data might be scaled, so a row with a sum near 1 is scaled up to 100).
# It returns:
# 1. Rows that meet the criteria (with scaling applied if needed).
# 2. Rows that do not meet the criteria.
def filter_rows_by_sum(dataframe: pd.DataFrame, tolerance=2):
    row_sums = dataframe.sum(axis=1)
    tol_100 = tolerance  # Tolerance for rows that should sum to 100
    tol_1 = tolerance / 100  # Tolerance for rows that should sum to 1 (after scaling)
    mask_sum_100 = row_sums.between(100 - tol_100, 100 + tol_100)
    mask_sum_1 = row_sums.between(1 - tol_1, 1 + tol_1)
    rows_sum_100 = dataframe.loc[mask_sum_100]
    rows_sum_1_scaled = dataframe.loc[mask_sum_1] * 100  # Scale rows summing to ~1 to be comparable
    combined_rows = pd.concat([rows_sum_100, rows_sum_1_scaled])
    excluded_rows = dataframe.drop(combined_rows.index)
    return combined_rows, excluded_rows

# -----------------------------------------------------------------------------
# Function: filter_columns_by_properties
# -----------------------------------------------------------------------------
# This function keeps only the columns whose names contain at least one of the
# specified property keywords (provided in a list).
# It returns:
# 1. A DataFrame with the columns that contain one of the properties.
# 2. A DataFrame with the columns that do not contain any of the properties.
def filter_columns_by_properties(dataframe: pd.DataFrame, properties: list):
    props_lower = [prop.lower() for prop in properties]
    def has_any_property(col_name: str) -> bool:
        col_lower = col_name.lower()
        return any(prop in col_lower for prop in props_lower)
    col_mask = [has_any_property(col) for col in dataframe.columns]
    filtered_dataframe = dataframe.loc[:, col_mask]
    excluded_dataframe = dataframe.loc[:, [not c for c in col_mask]]
    return filtered_dataframe, excluded_dataframe

# -----------------------------------------------------------------------------
# Function: remover_linhas_0
# -----------------------------------------------------------------------------
# This function removes rows from the DataFrame where the sum of values is 0.
# It returns:
# 1. A DataFrame with rows that have a non-zero sum.
# 2. A DataFrame with rows that were removed because they summed to 0.
def remover_linhas_0(dataframe: pd.DataFrame):
    row_sums = dataframe.sum(axis=1)
    not_null_rows_mask = (row_sums != 0)
    dataframe_without_null = dataframe.loc[not_null_rows_mask]
    dataframe_with_null = dataframe.loc[~not_null_rows_mask]
    return dataframe_without_null, dataframe_with_null

# -----------------------------------------------------------------------------
# Function: filter_columns_without_plus
# -----------------------------------------------------------------------------
# This function checks every column name and:
# - If a column name contains a '+' sign, it will be removed
#   unless it is recognized as a refractive index column.
# - It returns two DataFrames:
#   1. One with the columns kept.
#   2. One with the columns that were excluded.
def filter_columns_without_plus(dataframe: pd.DataFrame):
    filtered_cols = []
    excluded_cols = []
    for col in dataframe.columns:
        if "+" in col:
            if is_refractive_index_column(col):
                filtered_cols.append(col)
            else:
                excluded_cols.append(col)
        else:
            filtered_cols.append(col)
    return dataframe.loc[:, filtered_cols], dataframe.loc[:, excluded_cols]

# -----------------------------------------------------------------------------
# Function: remove_rows_with_nan
# -----------------------------------------------------------------------------
# This function removes any rows that contain missing values (NaN).
# It returns two DataFrames:
# 1. One with rows that do not contain NaN.
# 2. One with the rows that were removed (because they contain NaN).
def remove_rows_with_nan(dataframe: pd.DataFrame):
    has_nan_mask = dataframe.isna().any(axis=1)
    filtered_df = dataframe.loc[~has_nan_mask]
    excluded_df = dataframe.loc[has_nan_mask]
    return filtered_df, excluded_df

# =============================================================================
# Function: apply_all_filters_until_final
# =============================================================================
# This is the main function that applies all the filtering steps to the DataFrame.
# It follows these steps:
# 1) Saves and then removes the 'IDS' column temporarily.
# 2) Cleans the DataFrame by replacing unwanted characters and converting data to numbers.
# 3) Removes columns that contain only zeros.
# 4) Filters the columns to keep only those that are desired compounds.
# 5) Filters rows so that each row's sum is approximately 100 (or 1 scaled to 100).
# 6) Filters columns based on specific property keywords.
# 7) Removes rows from the property DataFrame that sum to 0.
# 8) Removes rows from the compounds DataFrame that are missing in the properties DataFrame.
# 9) Combines the compounds and properties data side by side.
# 10) Removes columns containing '+' (except for valid refractive index columns).
# 11) Removes any rows that still have missing values.
# 12) Re-adds the 'IDS' column.
def apply_all_filters_until_final(dataframe: pd.DataFrame, data: dict) -> pd.DataFrame:
    # 1) Save the 'IDS' column and remove it from the DataFrame
    column_ids = dataframe['IDS'].copy()
    dataframe.drop(columns=['IDS'], inplace=True)
    
    # 2) Basic cleaning of the DataFrame
    dataframe = clean_and_fill_zeros(dataframe)
    
    # 3) Remove columns that have only zeros
    dataframe, _ = remove_columns_with_only_zeros(dataframe)
    
    # 4) Filter columns to keep only desired compound columns
    desired_compounds = data["desired_compounds"]
    compounds_df, _ = filter_by_compounds(dataframe, desired_compounds)
    
    # 5) Filter rows that sum approximately to 100 (or ~1 scaled to 100)
    rows_sum_100_compounds, _ = filter_rows_by_sum(compounds_df)
    
    # 6) Filter columns to keep only those with certain properties
    properties = [
        "refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", 
        "devitrification", "point", "crystallization", "thermal", "mean", 
        "glass transition", "crystallinity", "electric", "onset", "transition", 
        "permittivity", "iso", "RI", "index", "ref", "nd", "η", "nm", "ratio", 
        "n5", "n6", "n7", "n8", "n9"
    ]
    properties_df, _ = filter_columns_by_properties(dataframe, properties)
    
    # 7) Remove rows in the properties DataFrame that sum to 0
    non_null_properties_rows, null_properties_rows = remover_linhas_0(properties_df)
    
    # 8) Remove from the compounds DataFrame the rows that have no properties
    rows_sum_100_compounds = rows_sum_100_compounds.loc[~rows_sum_100_compounds.index.isin(null_properties_rows.index)]
    
    # 9) Concatenate the compounds and properties DataFrames side by side
    compounds_and_properties = pd.concat([rows_sum_100_compounds, non_null_properties_rows], axis=1)
    
    # 10) Remove columns that contain '+' (except for valid refractive index columns)
    final_filtered, _ = filter_columns_without_plus(compounds_and_properties)
    
    # 11) Remove any rows that have missing values
    final_filtered, _ = remove_rows_with_nan(final_filtered)
    
    # 12) Reinsert the 'IDS' column back into the DataFrame
    final_filtered['IDS'] = column_ids.loc[final_filtered.index].values
    
    return final_filtered

# =============================================================================
# Main Execution Block
# =============================================================================
# This block of code runs when the script is executed directly.
if __name__ == "__main__":
    # Define the base path for the data folder
    BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data/patents"
    csv_path = BASE_PATH / "merged_df.csv"
    
    # Load the original DataFrame from a CSV file
    dataframe_original = pd.read_csv(csv_path, low_memory=False)
    
    # Read the JSON file that contains the desired properties
    json_path = Path("json/properties.json")
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Apply all filters to the DataFrame to generate the final filtered DataFrame
    final_df = apply_all_filters_until_final(dataframe_original, data)
    
    # Create the directory to save the filtered DataFrame (if it does not exist)
    filtered_path = Path("data/filtered")
    filtered_path.mkdir(parents=True, exist_ok=True)
    
    # Save the final DataFrame as a CSV file
    final_df.to_csv(filtered_path / "final_df.csv", index=False)
    
    # Print a success message with the shape (number of rows and columns) of the final DataFrame
    print(f"final_df.csv generated successfully: {final_df.shape[0]} rows and {final_df.shape[1]} columns.")
