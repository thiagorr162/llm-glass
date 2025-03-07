import json
import pandas as pd
from pathlib import Path
import re

# =============================================================================
# Cleaning and Filtering Functions
# =============================================================================

def clean_and_fill_zeros(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a DataFrame by:
      - Replacing any occurrence of '—' with 0.
      - Converting all columns to numeric (if possible).
      - Filling any missing values (NaN) with 0.
    """
    dataframe.replace('—', 0, inplace=True)
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

def remove_columns_with_only_zeros(dataframe: pd.DataFrame):
    """
    Removes columns that contain only zeros.
    Returns:
      - A DataFrame with columns that have at least one non-zero value.
      - A DataFrame with columns that were removed (only zeros).
    """
    not_all_zero_mask = (dataframe != 0).any(axis=0)
    filtered_dataframe = dataframe.loc[:, not_all_zero_mask]
    excluded_columns_df = dataframe.loc[:, ~not_all_zero_mask]
    return filtered_dataframe, excluded_columns_df

def filter_by_compounds(dataframe: pd.DataFrame, desired_compounds: list):
    """
    Keeps only the columns whose names are in the desired compounds list.
    Returns:
      - A DataFrame with only the desired compound columns.
      - A DataFrame with the columns that were not included.
    """
    desired_compounds_set = set(desired_compounds)
    filtered_columns_mask = dataframe.columns.isin(desired_compounds_set)
    filtered_df = dataframe.loc[:, filtered_columns_mask]
    excluded_df = dataframe.loc[:, ~filtered_columns_mask]
    return filtered_df, excluded_df

def filter_rows_by_sum(dataframe: pd.DataFrame, tolerance=2):
    """
    Keeps only the rows where the sum of values is approximately 100
    or approximately 1 (assuming the data might be scaled, so a row with a sum near 1 is scaled up to 100).
    Returns:
      - Rows that meet the criteria (with scaling applied if needed).
      - Rows that do not meet the criteria.
    """
    row_sums = dataframe.sum(axis=1)
    tol_100 = tolerance
    tol_1 = tolerance / 100
    mask_sum_100 = row_sums.between(100 - tol_100, 100 + tol_100)
    mask_sum_1 = row_sums.between(1 - tol_1, 1 + tol_1)
    rows_sum_100 = dataframe.loc[mask_sum_100]
    rows_sum_1_scaled = dataframe.loc[mask_sum_1] * 100
    combined_rows = pd.concat([rows_sum_100, rows_sum_1_scaled])
    excluded_rows = dataframe.drop(combined_rows.index)
    return combined_rows, excluded_rows

def filter_columns_by_properties(dataframe: pd.DataFrame, properties: list):
    """
    Keeps only the columns whose names contain at least one of the specified property keywords.
    Returns:
      - A DataFrame with the columns that contain one of the properties.
      - A DataFrame with the columns that do not contain any of the properties.
    """
    props_lower = [prop.lower() for prop in properties]
    def has_any_property(col_name: str) -> bool:
        return any(prop in col_name.lower() for prop in props_lower)
    col_mask = [has_any_property(col) for col in dataframe.columns]
    filtered_dataframe = dataframe.loc[:, col_mask]
    excluded_dataframe = dataframe.loc[:, [not flag for flag in col_mask]]
    return filtered_dataframe, excluded_dataframe

def remover_linhas_0(dataframe: pd.DataFrame):
    """
    Removes rows from the DataFrame where the sum of values is 0.
    Returns:
      - A DataFrame with rows that have a non-zero sum.
      - A DataFrame with rows that were removed because they summed to 0.
    """
    row_sums = dataframe.sum(axis=1)
    not_null_rows_mask = (row_sums != 0)
    dataframe_without_null = dataframe.loc[not_null_rows_mask]
    dataframe_with_null = dataframe.loc[~not_null_rows_mask]
    return dataframe_without_null, dataframe_with_null

def remove_rows_with_nan(dataframe: pd.DataFrame):
    """
    Removes any rows that contain missing values (NaN).
    Returns:
      - A DataFrame with rows that do not contain NaN.
      - A DataFrame with the rows that were removed.
    """
    has_nan_mask = dataframe.isna().any(axis=1)
    filtered_df = dataframe.loc[~has_nan_mask]
    excluded_df = dataframe.loc[has_nan_mask]
    return filtered_df, excluded_df

def exclude_plus_compound(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes columns from the DataFrame that belong to desired compounds and contain a '+' sign.
    The list of desired compounds is obtained from the JSON file 'json/properties.json'.
    """
    json_path = Path("json/properties.json")
    with open(json_path, 'r') as file:
        data = json.load(file)
    desired_compounds = data["desired_compounds"]
    compound_columns = [col for col in df.columns if col in desired_compounds]
    cols_with_plus = [col for col in compound_columns if '+' in col]
    return df.drop(columns=cols_with_plus)

def apply_all_filters_until_final(dataframe: pd.DataFrame, data: dict) -> pd.DataFrame:
    """
    Applies all filtering steps to the DataFrame:
      1) Save and remove the 'IDS' column temporarily.
      2) Clean the DataFrame.
      3) Remove columns that contain only zeros.
      4) Filter columns to keep only the desired compounds and remove, from those, columns containing '+'.
      5) Filter rows so that each row's sum is approximately 100 (or 1 scaled to 100).
      6) Filter columns based on specific property keywords.
      7) Remove rows from the property DataFrame that sum to 0.
      8) Remove from the compounds DataFrame the rows that have no properties.
      9) Concatenate the compounds and properties DataFrames side by side.
      10) Remove any rows that still have missing values.
      11) Reinsert the 'IDS' column.
    """
    # 1) Save and remove the 'IDS' column
    column_ids = dataframe['IDS'].copy()
    dataframe.drop(columns=['IDS'], inplace=True)
    
    # 2) Basic cleaning of the DataFrame
    dataframe = clean_and_fill_zeros(dataframe)
    
    # 3) Remove columns that have only zeros
    dataframe, _ = remove_columns_with_only_zeros(dataframe)
    
    # 4) Filter columns to keep only desired compounds
    desired_compounds = data["desired_compounds"]
    compounds_df, _ = filter_by_compounds(dataframe, desired_compounds)
    # Remove desired compound columns that contain '+'
    compounds_df = exclude_plus_compound(compounds_df)
    
    # 5) Filter rows that sum approximately to 100 (or 1 scaled to 100)
    rows_sum_100_compounds, _ = filter_rows_by_sum(compounds_df)
    
    # 6) Filter columns based on specific property keywords
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
    
    # 10) Remove any rows that have missing values
    final_filtered, _ = remove_rows_with_nan(compounds_and_properties)
    
    # 11) Reinsert the 'IDS' column
    final_filtered = final_filtered.copy()  # Ensure final_filtered is a new independent DataFrame
    final_filtered.loc[:, 'IDS'] = column_ids.loc[final_filtered.index].values
    
    return final_filtered

# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    # Define the base path for the data folder
    BASE_PATH = Path(__file__).resolve().parent.parent.parent / "data/patents"
    csv_path = BASE_PATH / "merged_df.csv"
    
    # Load the original DataFrame from a CSV file
    dataframe_original = pd.read_csv(csv_path, low_memory=False)
    
    # Read the JSON file that contains the desired compounds and properties
    json_path = Path("json/properties.json")
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Apply all filters to generate the final filtered DataFrame
    final_df = apply_all_filters_until_final(dataframe_original, data)
    
    # Create the directory to save the filtered DataFrame (if it does not exist)
    filtered_path = Path("data/filtered")
    filtered_path.mkdir(parents=True, exist_ok=True)
    
    # Save the final DataFrame as a CSV file
    final_df.to_csv(filtered_path / "final_df.csv", index=False)
    
    # Print a success message with the shape (number of rows and columns) of the final DataFrame
    print(f"final_df.csv generated successfully: {final_df.shape[0]} rows and {final_df.shape[1]} columns.")
