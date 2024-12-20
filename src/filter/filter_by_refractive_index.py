import json
import pandas as pd
from pathlib import Path
import re

BASE_PATH = Path("data/patents")
FILTERED_PATH = Path("data/filtered")

dataframe_C_and_R= pd.read_csv(FILTERED_PATH / "compounds_and_refractive_only_df.csv", low_memory=False)

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

def is_refractive_index_column(col_name: str) -> bool:
    """
    Determines if a column name is related to the refractive index.
    Excludes columns containing 'density'.
    Expands the original conditions to include variations like "Ref. Ind.", "Refr.index",
    "Index (@ 633 nm)", and others.
    """
    lower_name = col_name.lower()

    # Exclude columns related to density
    if 'density' in lower_name:
        return False

    # If the column contains "refrac" or "refractive"
    if "refrac" in lower_name:
        return True

    # Check for "ref." followed by "ind" as an abbreviation for "refractive index"
    # Examples: "Ref. Ind.", "Refr.ind", "Ref index", "Refr.index"
    if re.search(r"ref(\.?)(\s+)?ind", lower_name) or "refr.index" in lower_name:
        return True

    # Check for "ref" and "index" separated but within the same expression
    # e.g., "Ref Index", "Ref Index nd"
    if "ref" in lower_name and "index" in lower_name:
        return True

    # "ri" as a standalone word
    if re.search(r"\bri\b", lower_name):
        return True

    # "nd" or "nD" as standalone words
    if re.search(r"\bnd\b", lower_name, re.IGNORECASE):
        return True

    # "nXYZ" where XYZ are digits, indicating refractive index at a specific wavelength
    if re.search(r"\bn\d+(\.\d+)?\b", lower_name):
        return True

    # "n (at XXX nm)"
    if re.search(r"\bn\s*\(at\s*\d+\s*nm\)", lower_name):
        return True

    # Consider columns with "index" and a wavelength pattern like "(@ XXX nm)" as refractive index
    if "index" in lower_name and re.search(r"\(@\s*\d+\s*nm\)", lower_name):
        return True

    # Handle expressions like "ri @" within the name
    if re.search(r"ri\s*@", lower_name):
        return True

    return False

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

    # Agora utiliza a função aprimorada
    filtered_df = filtered_df[[col for col in filtered_df.columns if is_refractive_index_column(col)]]

    non_zero_counts = (filtered_df != 0).sum(axis=1)
    summed_refractive = filtered_df.sum(axis=1, skipna=True)
    summed_refractive[non_zero_counts > 1] = -1

    multiple_indices = filtered_df.where(non_zero_counts > 1, other=0)
    merged_df = pd.concat([
        original_df.drop(columns=filtered_df.columns),
        summed_refractive.rename("TERMINA AQUI / Refractive Index"),
        multiple_indices
    ], axis=1)
    
    refractive_only = pd.concat([
        compounds_df,
        summed_refractive.rename("TERMINA AQUI / Refractive Index"),
        multiple_indices
    ], axis=1)

    refractive_only = refractive_only[refractive_only["TERMINA AQUI / Refractive Index"] != 0]

    return merged_df, refractive_only

def New(compounds_and_refractive_only_df, filtered_path):
    """
    This function identifies columns related to the refractive index that are not in a standard format,
    extracts the corresponding IDs from rows that have values in these columns (different from zero),
    and generates a CSV file with this information.

    Parameters:
    - compounds_and_refractive_only_df: Filtered DataFrame containing compound and refractive index columns.
    - filtered_path: Path to the directory where the final CSV will be saved.

    Result:
    - Creates the file 'generic_refractive_ids.csv' in the specified directory, with one column for each 
      identified generic refractive index column, listing the corresponding IDs.
    """
    
    def is_standard_form(col_name: str) -> bool:
        """
        Checks if the column name represents a standard form of refractive index.
        Standard formats include 'nd', 'nf', 'n' followed by digits (e.g., 'n590', 'n600'),
        or patterns like 'n531.9 nm', 'n (at 633 nm)', etc.
        """
        lower_name = col_name.lower().strip()
        
        # Exact matches for 'nd' or 'nf'
        if re.fullmatch(r'nd', lower_name, re.IGNORECASE):
            return True
        if re.fullmatch(r'nf', lower_name, re.IGNORECASE):
            return True
        
        # 'n' followed by digits, possibly with decimals
        if re.fullmatch(r'n\d+(\.\d+)?', lower_name):
            return True
        
        # 'n' followed by digits + 'nm'
        if re.fullmatch(r'n\d+(\.\d+)?\s*nm', lower_name):
            return True
        
        # Pattern 'n (at XXX nm)'
        if re.fullmatch(r'n\s*\(at\s*\d+\s*nm\)', lower_name):
            return True
        
        # Pattern '(@ XXX nm)'
        if re.fullmatch(r'\(@\s*\d+\s*nm\)', lower_name):
            return True
        
        # 'nd' or 'nf' as whole words
        if re.search(r'\bnd\b', lower_name):
            return True
        if re.search(r'\bnf\b', lower_name):
            return True
        
        return False
    
    # Identify generic refractive index columns
    generic_refractive_cols = []
    for col in compounds_and_refractive_only_df.columns:
        if col.lower() == "ids":
            continue
        if col.strip().lower() == "termina aqui / refractive index":
            continue  # Exclude the column 'TERMINA AQUI / Refractive Index'
        if is_refractive_index_column(col) and not is_standard_form(col):
            generic_refractive_cols.append(col)

    # Dictionary to store IDs for each generic refractive index column
    generic_id_dict = {}
    for col in generic_refractive_cols:
        valid_rows = compounds_and_refractive_only_df[compounds_and_refractive_only_df[col] != 0]
        ids_list = valid_rows['IDS'].dropna().unique().tolist()
        generic_id_dict[col] = ids_list

    # Determine the maximum length of the ID lists
    max_len = max((len(ids) for ids in generic_id_dict.values()), default=0)

    # Create a dictionary with lists of equal length, padded with empty strings
    df_data = {}
    for col, ids in generic_id_dict.items():
        padded_ids = ids + [""] * (max_len - len(ids))
        df_data[col] = padded_ids

    # Create the resulting DataFrame
    generic_refractive_df = pd.DataFrame(df_data)

    # Save the DataFrame to CSV only if it contains data
    if not generic_refractive_df.empty:
        generic_refractive_df.to_csv(filtered_path / 'generic_refractive_ids.csv', index=False)


def is_standard_form(col_name: str) -> bool:
    """
    Checks if the column name represents a standard form of refractive index.
    Standard formats include 'nd', 'nf', 'n' followed by digits (e.g., 'n590', 'n600'),
    or patterns like 'n531.9 nm', 'n (at 633 nm)', etc.
    """
    lower_name = col_name.lower().strip()

    # Exact matches for 'nd' or 'nf'
    if re.fullmatch(r'nd', lower_name, re.IGNORECASE):
        return True
    if re.fullmatch(r'nf', lower_name, re.IGNORECASE):
        return True

    # 'n' followed by digits, possibly with decimals
    if re.fullmatch(r'n\d+(\.\d+)?', lower_name):
        return True

    # 'n' followed by digits + 'nm'
    if re.fullmatch(r'n\d+(\.\d+)?\s*nm', lower_name):
        return True

    # Pattern 'n (at XXX nm)'
    if re.fullmatch(r'n\s*\(at\s*\d+\s*nm\)', lower_name):
        return True

    # Pattern '(@ XXX nm)'
    if re.fullmatch(r'\(@\s*\d+\s*nm\)', lower_name):
        return True

    # 'nd' or 'nf' as whole words
    if re.search(r'\bnd\b', lower_name):
        return True
    if re.search(r'\bnf\b', lower_name):
        return True

    return False