import json
import pandas as pd
from pathlib import Path
import re

# -------------------------------------------------------------------------------
# Function: is_refractive_index_column
# -------------------------------------------------------------------------------
# This function checks if a column name is related to a refractive index.
# It does this by searching for key words in the column name.
def is_refractive_index_column(col_name: str) -> bool:
    lower_name = col_name.lower()
    if 'density' in lower_name:
        return False
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

# -------------------------------------------------------------------------------
# Function: append_type_by_id
# -------------------------------------------------------------------------------
# Enriches the given DataFrame by looking up each row’s 'IDS' in the classifications_df.
def append_type_by_id(df: pd.DataFrame,
                      classifications_df: pd.DataFrame
                     ) -> pd.DataFrame:
    type_map = dict(zip(classifications_df['IDS'], classifications_df['Type']))
    # map will return None for any IDS not in the map
    df['Type'] = df['IDS'].map(type_map)
    return df

# -------------------------------------------------------------------------------
# Function: filter_by_compounds
# -------------------------------------------------------------------------------
# This function keeps only the columns in the DataFrame that match the desired_compounds list.
# It returns two DataFrames:
#   1. One with the columns in the desired list.
#   2. One with the columns not in the desired list.
def filter_by_compounds(dataframe: pd.DataFrame,
                        desired_compounds: list[str]
                       ) -> tuple[pd.DataFrame, pd.DataFrame]:
    filtered_columns = [col for col in dataframe.columns if col in desired_compounds]
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

# -------------------------------------------------------------------------------
# Function: merge_refractive_index_columns
# -------------------------------------------------------------------------------
# Combines multiple refractive index (RI) columns into a single "Summarized Refractive Index" column.
def merge_refractive_index_columns(dataframe: pd.DataFrame,
                                   desired_compounds: list[str]
                                  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    # 1. Snapshot original for output
    original_df = dataframe.copy()
    
    # 2. Isolate compound columns for the "refractive_only" output
    compounds_df, _ = filter_by_compounds(dataframe, desired_compounds)

    # 3. Temporarily drop any columns where values <1 or >5 (assumed out-of-range RI)
    mask_out_of_range = (dataframe != 0) & ((dataframe < 1) | (dataframe > 5))
    cols_to_drop = mask_out_of_range.any(axis=0)
    filtered_df = dataframe.loc[:, ~cols_to_drop]

    # 4. Exclude compound columns to isolate only RI-related columns
    filtered_df = filtered_df[[c for c in filtered_df.columns if c not in desired_compounds]]
    
    # 5. Identify actual RI columns via helper
    ri_df = filtered_df[[c for c in filtered_df.columns if is_refractive_index_column(c)]]

    # 6. Count non-zero RIs per row and sum them
    non_zero_counts = (ri_df != 0).sum(axis=1)
    summed_refractive = ri_df.sum(axis=1, skipna=True)
    # If more than one non-zero RI in a row, mark as conflict
    summed_refractive[non_zero_counts > 1] = -1

    # 7. Build the merged DataFrame: drop original RI cols, add the merged column
    merged_df = pd.concat([
        original_df.drop(columns=ri_df.columns),
        summed_refractive.rename("Summarized Refractive Index")
    ], axis=1)

    # 8. Build the "refractive_only" DataFrame
    refractive_only = pd.concat([
        compounds_df,
        ri_df,
        summed_refractive.rename("Summarized Refractive Index")
    ], axis=1)
    # Optional: drop rows without any RI data
    refractive_only = refractive_only[refractive_only["Summarized Refractive Index"] != 0]

    return merged_df, refractive_only

# -------------------------------------------------------------------------------
# Main Execution Block
# -------------------------------------------------------------------------------
if __name__ == "__main__":
    # Paths
    filtered_path      = Path("data/filtered")
    final_df_path      = filtered_path / "final_df.csv"
    classifications_path = filtered_path / "classifications.csv"
    json_path          = Path("json/properties.json")

    # 1. Load data
    final_df           = pd.read_csv(final_df_path)
    classifications_df = pd.read_csv(classifications_path)

    # 2. Enrich with 'Type'
    final_df = append_type_by_id(final_df, classifications_df)

    # 3. Load desired compounds list
    with json_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    desired_compounds = data["desired_compounds"]

    # 4. Merge RI columns
    final_df_atualizado, compounds_and_refractive_only = \
        merge_refractive_index_columns(final_df, desired_compounds)

    # 5. Save both outputs
    final_df_atualizado.to_csv(filtered_path / "final_df_atualizado.csv", index=False)
    compounds_and_refractive_only.to_csv(filtered_path / "compounds_and_refractive.csv", index=False)
    print("Saved 'final_df_atualizado.csv' and 'compounds_and_refractive.csv' successfully.")