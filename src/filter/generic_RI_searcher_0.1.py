import pandas as pd
import re
from pathlib import Path

# -----------------------------
# 1. Define Base Paths
# -----------------------------
# BASE_PATH points to the directory where raw patent data might reside.
# FILTERED_PATH points to the directory containing the filtered data.
BASE_PATH = Path("data/patents")
FILTERED_PATH = Path("data/filtered")

# -----------------------------
# 2. Regex Pattern for Standard Forms
# -----------------------------
# This regex defines what we consider as "standard forms" of refractive index column names.
# It matches:
#   - 'nd', 'nf'
#   - 'n' followed by digits, optionally with decimals (e.g., n600, n600.5)
#   - 'n' followed by digits + 'nm' (e.g., n633nm, n600.5 nm)
#   - 'n (at XXX nm)' (e.g., n (at 633 nm))
#   - '(@ XXX nm)' (e.g., (@ 633 nm))
#   - or any string that contains 'nd' or 'nf' as whole words
STANDARD_FORM_REGEX = re.compile(
    r'^('
        r'nd|nf|'                             # Exactly 'nd' or 'nf'
        r'n\d+(\.\d+)?|'                      # 'n' followed by digits (with optional decimal)
        r'n\d+(\.\d+)?\s*nm|'                 # 'n' + digits + 'nm'
        r'n\s*\(at\s*\d+\s*nm\)|'             # 'n (at XXX nm)'
        r'\(@\s*\d+\s*nm\)'                   # '(@ XXX nm)'
    r')$|.*\b(nd|nf)\b.*$', 
    re.IGNORECASE
)

def is_standard_form(col_name: str) -> bool:
    """
    Checks if a column name matches one of the standard refractive index (RI) formats.
    
    Standard formats include:
      - 'nd', 'nf'
      - 'n' followed by digits, optionally with decimal (e.g. 'n590', 'n600.5')
      - 'n' followed by digits and 'nm' (e.g., 'n590nm', 'n600.5 nm')
      - 'n (at XXX nm)' (e.g., 'n (at 633 nm)')
      - '(@ XXX nm)' (e.g., '(@ 633 nm)')
      - Contains the whole words 'nd' or 'nf' anywhere in the string
    
    Returns:
    - True if the column name matches a standard format, False otherwise.
    """
    lower_name = col_name.lower().strip()
    return bool(STANDARD_FORM_REGEX.match(lower_name))

def is_refractive_index_column(col_name: str) -> bool:
    """
    Determines if a column name is related to the refractive index.
    Excludes columns containing 'density'.
    Expands original conditions to include terms like "Ref. Ind.", "Refr.index",
    "Index (@ 633 nm)", and other patterns.

    Parameters:
    - col_name (str): The column name to be checked.

    Returns:
    - bool: True if the column name is recognized as related to refractive index, False otherwise.
    """
    lower_name = col_name.lower()

    # Exclude columns related to 'density'
    if 'density' in lower_name:
        return False

    # If the column contains "refrac" or "refractive"
    if "refrac" in lower_name:
        return True

    # Check for "ref." followed by "ind" (e.g., "Ref. Ind.", "Refr.ind", "Refr.index")
    if re.search(r"ref(\.?)(\s+)?ind", lower_name) or "refr.index" in lower_name:
        return True

    # Check if "ref" and "index" both appear
    if "ref" in lower_name and "index" in lower_name:
        return True

    # "ri" as a standalone word
    if re.search(r"\bri\b", lower_name):
        return True

    # "nd" (case-insensitive) as a standalone word
    if re.search(r"\bnd\b", lower_name, re.IGNORECASE):
        return True

    # Pattern like "n123" or "n123.45"
    if re.search(r"\bn\d+(\.\d+)?\b", lower_name):
        return True

    # "n (at XXX nm)" pattern
    if re.search(r"\bn\s*\(at\s*\d+\s*nm\)", lower_name):
        return True

    # Combination of "index" with a wavelength pattern like "(@ XXX nm)"
    if "index" in lower_name and re.search(r"\(@\s*\d+\s*nm\)", lower_name):
        return True

    # Expression like "ri @" in the name
    if re.search(r"ri\s*@", lower_name):
        return True

    return False

def Nova(compounds_and_refractive_only_df: pd.DataFrame, filtered_path: Path):
    """
    Identifies generic (non-standard) refractive index columns in the provided DataFrame
    and creates a CSV listing the IDs (from the 'IDS' column) of rows that have non-zero
    values in those columns.

    Parameters:
    - compounds_and_refractive_only_df (pd.DataFrame): The DataFrame containing compound data
      and refractive index columns (usually 'compounds_and_refractive_only_df.csv').
    - filtered_path (Path): Path to the directory where the resulting CSV will be saved.

    Result:
    - Creates 'generic_refractive_ids.csv' in the specified directory, with one column for
      each identified generic refractive index column, listing the row IDs that have non-zero
      values in that column.
    """

    # 1. Identify generic RI columns that are recognized as refractive index but are NOT in a standard form.
    generic_refractive_cols = [
        col for col in compounds_and_refractive_only_df.columns
        if col.lower() != "ids"
        and col.strip().lower() != "termina aqui / refractive index"
        and is_refractive_index_column(col)
        and not is_standard_form(col)
    ]

    # If there are no generic (non-standard) RI columns, print a message and exit.
    if not generic_refractive_cols:
        print("No generic refractive index columns found.")
        return

    # 2. For each generic refractive index column, find the row IDs where the column is not zero.
    generic_id_dict = {
        col: compounds_and_refractive_only_df.loc[
                compounds_and_refractive_only_df[col] != 0, 'IDS'
            ].dropna().unique().tolist()
        for col in generic_refractive_cols
    }

    # If no rows have non-zero values in these columns, print a message and exit.
    if not generic_id_dict:
        print("No non-zero IDs found for the generic refractive index columns.")
        return

    # 3. Determine the maximum length among all ID lists to align them in a DataFrame.
    max_len = max((len(ids) for ids in generic_id_dict.values()), default=0)

    # 4. Create a dictionary suitable for building a DataFrame, ensuring all columns have equal length.
    df_data = {
        col: ids + [""] * (max_len - len(ids))  # Fill shorter lists with empty strings
        for col, ids in generic_id_dict.items()
    }

    # 5. Create the DataFrame from this dictionary.
    generic_refractive_df = pd.DataFrame(df_data)

    # 6. Save the DataFrame to CSV if it has any data.
    if not generic_refractive_df.empty:
        output_file = filtered_path / 'generic_refractive_ids.csv'
        generic_refractive_df.to_csv(output_file, index=False)
        print(f"Generic refractive index IDs saved to {output_file}")
    else:
        print("No data to save for generic refractive index IDs.")

def main():
    """
    Main function to execute the script workflow:
    - Reads the DataFrame from 'compounds_and_refractive_only_df.csv' (in data/filtered/).
    - Calls the 'Nova' function to identify and list non-standard refractive index columns with non-zero entries.
    - Saves the resulting list into 'generic_refractive_ids.csv'.
    """
    # Define the path to the CSV file we want to analyze
    input_csv_path = FILTERED_PATH / "compounds_and_refractive_only_df.csv"

    # Check if the file exists
    if not input_csv_path.is_file():
        print(f"File not found: {input_csv_path}")
        return

    # Attempt to load the DataFrame from the CSV
    try:
        df = pd.read_csv(input_csv_path)
        print(f"CSV '{input_csv_path}' successfully loaded.")
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # Use the same folder as the input file for saving results
    filtered_path = input_csv_path.parent

    # Call the 'Nova' function to process non-standard refractive index columns
    Nova(df, filtered_path)

# Execute the main function if the script is run directly.
if __name__ == "__main__":
    main()
