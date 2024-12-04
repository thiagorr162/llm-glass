import json
import pandas as pd
from pathlib import Path
import re

# Define base paths
BASE_PATH = Path("data/patents")
FILTERED_PATH = Path("data/filtered")

# Load data
csv_path = BASE_PATH / "merged_df.csv"
dataframe_original = pd.read_csv(csv_path, low_memory=False)
json_path = Path("json/properties.json")
with open(json_path, 'r') as file:
    data = json.load(file)

def filter_by_compounds(dataframe):
    """
    Filters columns based on a predefined list of desired compounds.
    Returns:
    - Filtered DataFrame with desired compounds.
    - DataFrame with excluded columns.
    """
    desired_compounds = data["desired_compounds"]
    filtered_columns = [col for col in dataframe.columns if col in desired_compounds]
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

def filter_columns_without_plus(dataframe):
    """
    Filters columns based on whether their names contain the '+' character.
    Returns:
    - Filtered DataFrame (columns without '+').
    - DataFrame with excluded columns (containing '+').
    """
    filtered_columns = [col for col in dataframe.columns if "+" not in col]
    excluded_columns = [col for col in dataframe.columns if "+" in col]
    return dataframe[filtered_columns], dataframe[excluded_columns]

def clean_and_fill_zeros(dataframe):
    """
    Replaces '—' and NaN values with 0, and ensures all data is numeric.
    """
    dataframe = dataframe.replace('—', 0).fillna(0)
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

def remove_columns_with_only_zeros(dataframe):
    """
    Removes columns that contain only zeros.
    Returns:
    - DataFrame without columns containing only zeros.
    - DataFrame with excluded columns.
    """
    empty_columns = dataframe.columns[(dataframe == 0).all()]
    excluded_columns_df = dataframe[empty_columns]
    filtered_dataframe = dataframe.drop(columns=empty_columns)
    return filtered_dataframe, excluded_columns_df

def filter_rows_by_sum(dataframe, tolerance=2):
    """
    Filters rows based on their sum.
    Rows summing close to 100 are kept, and rows summing close to 1 are scaled to 100.
    Returns:
    - DataFrame with rows summing approximately to 100.
    - DataFrame with excluded rows.
    """
    row_sums = dataframe.sum(axis=1)
    tolerance_100 = tolerance
    tolerance_1 = tolerance / 100

    mask_sum_100 = (row_sums >= 100 - tolerance_100) & (row_sums <= 100 + tolerance_100)
    mask_sum_1 = (row_sums >= 1 - tolerance_1) & (row_sums <= 1 + tolerance_1)

    rows_sum_100 = dataframe.loc[mask_sum_100]
    rows_sum_1_scaled = dataframe.loc[mask_sum_1] * 100

    combined_rows = pd.concat([rows_sum_100, rows_sum_1_scaled])
    excluded_rows = dataframe.drop(combined_rows.index)

    return combined_rows, excluded_rows

def filter_columns_by_properties(dataframe):
    """
    Filters columns based on a predefined list of properties.
    Returns:
    - DataFrame with columns matching properties.
    - DataFrame with excluded columns.
    """
    properties = ["refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", 
                  "devitrification", "point", "crystallization", "thermal", "mean", 
                  "glass transition", "crystallinity", "electric", "onset", "transition", 
                  "permittivity", "iso", "RI", "index", "ref", "nd", "η", "nm", "ratio", 
                  "n5", "n6", "n7", "n8", "n9"]
    filtered_columns = [col for col in dataframe.columns if any(prop.lower() in col.lower() for prop in properties)]
    filtered_dataframe = dataframe[filtered_columns]
    excluded_dataframe = dataframe.drop(columns=filtered_columns)
    return filtered_dataframe, excluded_dataframe

def remove_rows_with_nan(dataframe):
    """
    Removes rows containing NaN values.
    Returns:
    - DataFrame without NaN rows.
    - DataFrame with excluded rows.
    """
    filtered_df = dataframe.dropna()
    excluded_df = dataframe.loc[dataframe.isna().any(axis=1)]
    return filtered_df, excluded_df

def merge_refractive_index_columns(dataframe):
    """
    Merges refractive index columns into a single column.
    Returns:
    - DataFrame with merged refractive index columns.
    - DataFrame with only refractive index columns.
    """
    original_df = dataframe.copy()
    compounds_df, _ = filter_by_compounds(dataframe)

    mask_out_of_range = (dataframe != 0) & ((dataframe < 1) | (dataframe > 5))
    columns_to_drop = mask_out_of_range.any(axis=0)
    filtered_df = dataframe.loc[:, ~columns_to_drop]

    desired_compounds = data["desired_compounds"]
    filtered_df = filtered_df[[col for col in filtered_df.columns if col not in desired_compounds]]

    def is_refractive_index_column(col_name):
        if 'density' in col_name.lower():
            return False
        return bool(re.search(r'(N|RI)', col_name, re.IGNORECASE)) or bool(re.search(r'refrac', col_name, re.IGNORECASE))

    filtered_df = filtered_df[[col for col in filtered_df.columns if is_refractive_index_column(col)]]

    non_zero_counts = (filtered_df != 0).sum(axis=1)
    summed_refractive = filtered_df.sum(axis=1, skipna=True)
    summed_refractive[non_zero_counts > 1] = -1

    multiple_indices = filtered_df.where(non_zero_counts > 1, other=0)
    merged_df = pd.concat([original_df.drop(columns=filtered_df.columns), summed_refractive.rename("TERMINA AQUI / Refractive Index"), multiple_indices], axis=1)
    refractive_only = pd.concat([compounds_df, summed_refractive.rename("TERMINA AQUI / Refractive Index"), multiple_indices], axis=1)

    return merged_df, refractive_only

def remover_linhas_0(dataframe):
    """
    Removes rows where the sum is equal to 0.
    Returns:
    - DataFrame with only non-null rows.
    - DataFrame with only null rows.
    """
    dataframe_without_null_rows = dataframe[dataframe.sum(axis=1) != 0]
    dataframe_with_null_rows = dataframe[dataframe.sum(axis=1) == 0]
    return dataframe_without_null_rows, dataframe_with_null_rows

def apply_all_filters(dataframe):
    """
    Applies all filtering steps to the DataFrame.
    Returns:
    - Filtered DataFrame.
    - Additional DataFrames representing excluded data at each step.
    """
    column_ids = dataframe.pop('IDS')  # Remove and store the IDS column from the original dataframe  
    
    dataframe = clean_and_fill_zeros(dataframe)  # Replace '—' and NaN with 0
    dataframe, excluded_empty = remove_columns_with_only_zeros(dataframe)  # Remove columns with only 0
    compounds_df, _ = filter_by_compounds(dataframe)  # Generate dataframe with only compounds
    rows_sum_100_compounds, excluded_sum = filter_rows_by_sum(compounds_df)  # Generate dataframe with compounds summing to 100
    properties_df, _ = filter_columns_by_properties(dataframe)  # Generate dataframe with only properties
    non_null_properties_rows, null_properties_rows = remover_linhas_0(properties_df)  # Remove null rows from properties 
    rows_sum_100_compounds_original = rows_sum_100_compounds.copy()  # *Correction: Preserve an original copy*
    rows_sum_100_compounds = rows_sum_100_compounds[~rows_sum_100_compounds.index.isin(null_properties_rows.index)]  # Remove compounds without properties
    compounds_and_properties = pd.concat([rows_sum_100_compounds, non_null_properties_rows], axis=1)  # Concatenate compounds and properties df
    final_filtered, excluded_plus = filter_columns_without_plus(compounds_and_properties)
    final_filtered, excluded_nan = remove_rows_with_nan(final_filtered)
    final_filtered, refractive_only = merge_refractive_index_columns(final_filtered)

    # Select compounds without properties from the original copy
    compounds_without_properties = rows_sum_100_compounds_original[rows_sum_100_compounds_original.index.isin(null_properties_rows.index)]
    dataframe_compounds_without_properties = pd.concat([compounds_without_properties, null_properties_rows], axis=1)
    # Use .loc to align IDs with the DataFrame indices
    dataframe_compounds_without_properties['IDS'] = column_ids.loc[dataframe_compounds_without_properties.index].values
    final_filtered['IDS'] = column_ids.loc[final_filtered.index].values  # *Correction: Use .loc for correct alignment*
    refractive_only['IDS'] = column_ids.loc[refractive_only.index].values
    return final_filtered, excluded_empty, excluded_sum, excluded_plus, excluded_nan, refractive_only, dataframe_compounds_without_properties


# Applying all filters to the original DataFrame
final_filtered, excluded_by_removeemptycolumns, excluded_by_sumlines, excluded_by_filterbynotplus, excluded_by_removerowswithna, compounds_and_refractive_only_df, dataframe_compounds_without_properties = apply_all_filters(dataframe_original)

# Saving the results to CSV files
filtered_path = Path("data/filtered")
final_filtered.to_csv(filtered_path / 'final_df.csv', index=False)
excluded_by_removeemptycolumns.to_csv(filtered_path / 'excluded_by_removeemptycolumns.csv', index=False)
excluded_by_sumlines.to_csv(filtered_path / 'excluded_by_sumlines.csv', index=False)
excluded_by_filterbynotplus.to_csv(filtered_path / 'excluded_by_filterbynotplus.csv', index=False)
excluded_by_removerowswithna.to_csv(filtered_path / 'excluded_by_removerowswithna.csv', index=False)
compounds_and_refractive_only_df.to_csv(filtered_path / 'compounds_and_refractive_only_df.csv', index=False)
dataframe_compounds_without_properties.to_csv(filtered_path / 'dataframe_compounds_without_properties.csv', index=False)

# Displaying processing summary
print("\nProcessing Summary:")
print(f"{'Original DataFrame size:':<50} {dataframe_original.shape}")
print(f"{'Final filtered DataFrame size:':<50} {final_filtered.shape}")
print(f"{'Excluded (empty columns):':<50} {excluded_by_removeemptycolumns.shape}")
print(f"{'Excluded (row sums):':<50} {excluded_by_sumlines.shape}")
print(f"{'Excluded (columns containing +):':<50} {excluded_by_filterbynotplus.shape}")
print(f"{'Excluded (rows with NaN):':<50} {excluded_by_removerowswithna.shape}")
print(f"{'DataFrame with compounds and refractive indices:':<50} {compounds_and_refractive_only_df.shape}")
print(f"{'DataFrame with compounds without properties:':<50} {dataframe_compounds_without_properties.shape}") 
