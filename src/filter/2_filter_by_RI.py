import json
import pandas as pd
from pathlib import Path
import re

# -----------------------------------------------------------------------------
# 1. Function: is_refractive_index_column
# -----------------------------------------------------------------------------

def is_refractive_index_column(col_name: str) -> bool:
    """
 This function checks if a column name is related to a refractive index.
 It does this by searching for key words in the column name.
    """
    lower_name = col_name.lower()  # Convert the column name to lowercase
    if 'density' in lower_name:
        return False  # Ignore columns related to 'density'
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

# -----------------------------------------------------------------------------
# 2. Function: filter_by_compounds
# -----------------------------------------------------------------------------

def filter_by_compounds(dataframe, desired_compounds):
    """
 This function keeps only the columns in the DataFrame that match the desired compounds list.
 It returns two DataFrames:
  1. One with the columns that are in the desired list.
 2. One with the columns that are not in the desired list.
    """
    
    filtered_columns = [col for col in dataframe.columns if col in desired_compounds]
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

# -----------------------------------------------------------------------------
# 3. Function: merge_refractive_index_columns
# -----------------------------------------------------------------------------

def merge_refractive_index_columns(dataframe, desired_compounds):
    """
 This function combines multiple refractive index (RI) columns into a single column.
 It follows these steps:
 1. Makes a copy of the original DataFrame.
 2. Separates the compound columns (which are not RI columns).
 3. Removes temporarily any columns with values "out of range" (values less than 1 or greater than 5).
 4. Excludes desired compound columns to isolate only RI columns.
 5. Sums the RI columns row by row. If more than one RI value is non-zero in a row,
    it sets the result to -1 (indicating ambiguity).
 6. Replaces the original RI columns with the new merged RI column.
 7. Creates a DataFrame that includes the compounds, original RI columns, and the merged RI column.
 8. Optionally, removes rows with no RI data (merged RI column equals 0).
    """
    
    # Make a copy of the original dataframe for safe processing
    original_df = dataframe.copy()
    
    # Get only the compound columns (the RI columns are not in desired_compounds)
    compounds_df, _ = filter_by_compounds(dataframe, desired_compounds)

    # Identify and temporarily remove columns with out of range values (<1 or >5)
    mask_out_of_range = (dataframe != 0) & ((dataframe < 1) | (dataframe > 5))
    columns_to_drop = mask_out_of_range.any(axis=0)
    filtered_df = dataframe.loc[:, ~columns_to_drop]

    # Exclude the compound columns to isolate the RI columns
    filtered_df = filtered_df[[col for col in filtered_df.columns if col not in desired_compounds]]
    # Extract only the refractive index (RI) columns using our helper function
    ri_df = filtered_df[[col for col in filtered_df.columns if is_refractive_index_column(col)]]

    # Count how many non-zero RI values exist in each row and sum the RI values
    non_zero_counts = (ri_df != 0).sum(axis=1)
    summed_refractive = ri_df.sum(axis=1, skipna=True)
    # If a row has more than one non-zero RI value, set the merged value to -1 (indicating a conflict)
    summed_refractive[non_zero_counts > 1] = -1

    # Create a new DataFrame (merged_df) by dropping the original RI columns
    # and adding the merged RI column (renamed as "Summarized Refractive Index")
    merged_df = pd.concat([
        original_df.drop(columns=ri_df.columns),
        summed_refractive.rename("Summarized Refractive Index")
    ], axis=1)

    # Build a DataFrame that includes:
    #   - The compound columns,
    #   - The original RI columns,
    #   - The merged RI column.
    refractive_only = pd.concat([
        compounds_df,
        ri_df,
        summed_refractive.rename("Summarized Refractive Index")
    ], axis=1)
    # Optionally, remove rows where the merged RI column is 0 (indicating no RI data available)
    refractive_only = refractive_only[refractive_only["Summarized Refractive Index"] != 0]

    return merged_df, refractive_only

# -----------------------------------------------------------------------------
# 4. Main Execution Block
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # 1. Define the path where the filtered final DataFrames live
    filtered_path = Path("data/filtered")
    
    # 2. Load the JSON file that contains the desired compounds
    json_path = Path("json/properties.json")
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    desired_compounds = data["desired_compounds"]
    
    # 3. Process both LEFT and RIGHT final DataFrames
    for side in ("LEFT", "RIGHT"):
        # Find the final_df file generated previously (e.g., "LEFT_Final_df(123x12).csv")
        final_files = list(filtered_path.glob(f"{side}_Final_df*.csv"))
        if not final_files:
            print(f"No final_df file found for {side}. Skipping.")
            continue
        final_path = final_files[0]
    
        # Load the final DataFrame from CSV
        final_df = pd.read_csv(final_path, low_memory=False)
    
        # Save and remove the 'IDS' column for processing
        ids_series = final_df['IDS'].copy()
        final_df.drop(columns=['IDS'], inplace=True)
    
        # Apply refractive-index merge to produce two DataFrames
        updated_df, compounds_and_refractive_only = merge_refractive_index_columns(final_df, desired_compounds)
    
        # Reinsert the 'IDS' column into both results
        updated_df['IDS'] = ids_series.loc[updated_df.index].values
        compounds_and_refractive_only['IDS'] = ids_series.loc[compounds_and_refractive_only.index].values
    
        # Save the compounds_and_refractive_only with shape in the filename
        r, c = compounds_and_refractive_only.shape
        out_name = f"{side}_compounds_and_refractive({r}x{c}).csv"
        compounds_and_refractive_only.to_csv(filtered_path / out_name, index=False)
    
        # Print success message
        print(f"{out_name} generated successfully: {r} rows and {c} columns.")
    
    print("All compounds_and_refractive_only files generated successfully.")
