import json
import pathlib
import re
import unicodedata
import shutil
import pandas as pd
import csv

# Function to normalize strings: removes spaces, accents, and converts to lowercase
def normalize_string(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s)
                  .encode("ASCII", "ignore").decode("utf-8").lower())

# Function to check if a value is numeric
def is_numeric(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

# Function to copy unprocessed files to a destination folder
def copy_to_not_processed(src_path, dest_folder):
    destination = dest_folder / src_path.name
    counter = 1

    # Adds a numeric suffix if the file already exists to avoid overwriting
    while destination.exists():
        destination = dest_folder / f"{src_path.stem}_{counter}{src_path.suffix}"
        counter += 1

    try:
        shutil.copy(src_path, destination)
        print(f"File copied to: {destination}")
    except Exception as e:
        print(f"Failed to copy {src_path} to 'not_processed': {e}")

# Configuration of paths
input_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")
not_processed_path = input_path / "not_processed"
not_processed_path.mkdir(parents=True, exist_ok=True)

# Load desired compounds from the JSON file and normalize the names
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) 
                         for compound in properties_data.get("desired_compounds", [])]

# Iterate through all CSV files in the specified structure
for table_file in input_path.rglob("*/processed/splitted/*.csv"):
    try:
        # Read the CSV file into lines
        with open(table_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Determine the maximum number of columns
        max_columns = max(len(row) for row in rows)

        # List to store information about each row
        rows_info = []
        max_first_numeric_idx = 0

        # Analyze each row to identify the position of the first numeric value
        for row in rows:
            first_numeric_idx = None
            for idx, val in enumerate(row):
                val_strip = val.strip()
                if val_strip in ['', '-', ' ']:
                    continue  # NaN value
                elif is_numeric(val_strip):
                    first_numeric_idx = idx
                    break  # First numeric value found
            if first_numeric_idx is None:
                first_numeric_idx = len(row)  # No numeric value found
            if first_numeric_idx > max_first_numeric_idx:
                max_first_numeric_idx = first_numeric_idx
            rows_info.append({
                'row': row,
                'first_numeric_idx': first_numeric_idx
            })

        # Adjust each row based on the maximum index of the first numeric value
        adjusted_rows = []
        for info in rows_info:
            row = info['row']
            first_numeric_idx = info['first_numeric_idx']
            shift = max_first_numeric_idx - first_numeric_idx
            if shift > 0:
                # Insert NaNs to align numeric values
                row = row + ['-'] * shift
            # Fill with NaNs to the right to ensure the same number of columns
            row += ['-'] * (max_columns - len(row))
            adjusted_rows.append(row)

        # Rewrite the CSV file with the adjusted rows
        with open(table_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(adjusted_rows)

        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(table_file, encoding='utf-8', delimiter=',', header=None)
        df = df.dropna(axis=1, how="all").T  # Remove completely empty columns and transpose

        # Find the header index containing the desired compounds
        header_idx = next(
            (idx for idx, row in enumerate(df.values)
             if any(normalize_string(str(h)) in desired_compounds for h in row)),
            None
        )

        if header_idx is not None:
            # Create a new DataFrame using the found header
            new_header = df.iloc[header_idx]
            new_df = df[header_idx + 1:].copy()
            new_df.columns = new_header

            # Add a column with the current file path
            new_df['IDS'] = str(table_file)

            # Define the output path to save the processed DataFrame
            output_path = table_file.parents[1] / "dataframe"
            output_path.mkdir(parents=True, exist_ok=True)
            new_df.to_csv(output_path / (table_file.stem + ".csv"), index=False)
        else:
            # Move the file to 'not_processed' if no desired compound is found in the header
            print(f"WARNING: No desired compound found in the header: {table_file}")
            copy_to_not_processed(table_file, not_processed_path)

    except Exception as e:
        # General error handling
        print(f"ERROR: {e} in {table_file}")
        copy_to_not_processed(table_file, not_processed_path)

# Final message indicating that processing is complete
print("Operation completed successfully.")
