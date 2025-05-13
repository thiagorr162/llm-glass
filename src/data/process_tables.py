import json
import pathlib
import re
import unicodedata
import shutil
import pandas as pd
import csv
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. Utility Functions
# ------------------------------------------------------------------------------

def normalize_string(s):
    """
    Normalize the input string by:
      - Decomposing Unicode characters and removing diacritics
      - Encoding to ASCII and ignoring non-ASCII characters
      - Decoding back to UTF-8
      - Converting to lowercase
      - Removing all whitespace
    Returns the canonical form to facilitate consistent comparisons.
    """
    return re.sub(
        r"\s+", "",
        unicodedata.normalize("NFKD", s)
                   .encode("ASCII", "ignore")
                   .decode("utf-8")
                   .lower()
    )

def is_numeric(val):
    """
    Determine if the string *val* can be parsed as a float.
    Returns True for valid numeric strings, False otherwise.
    """
    try:
        float(val)
        return True
    except ValueError:
        return False

def copy_to_not_processed(src_path: Path, dest_folder: Path):
    """
    Copy the file at *src_path* into *dest_folder*, avoiding name collisions by
    appending an incremental suffix if needed.
    Logs the destination or any error encountered.
    """
    destination = dest_folder / src_path.name
    counter = 1
    # If a file with the same name exists, append _1, _2, etc., until unique
    while destination.exists():
        destination = dest_folder / f"{src_path.stem}_{counter}{src_path.suffix}"
        counter += 1
    try:
        shutil.copy(src_path, destination)
        print(f"Arquivo copiado para: {destination}")
    except Exception as e:
        print(f"Falha ao copiar {src_path} para 'not_processed': {e}")

# ------------------------------------------------------------------------------
# 2 Path and configuration and Initialization
# ------------------------------------------------------------------------------
a_input_path = pathlib.Path("data/patents")   # Base directory for patent tables
properties_file = pathlib.Path("json/properties.json")  # JSON file listing target compounds
not_processed_path = a_input_path / "not_processed"  # Directory for unprocessed files
not_processed_path.mkdir(parents=True, exist_ok=True)  # Ensure existence

# Load and normalize desired compound names from JSON
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = set(
        normalize_string(comp) for comp in properties_data.get("desired_compounds", [])
    )

# ------------------------------------------------------------------------------
# 3. RIGHT-Edge Table Processing Logic
# ------------------------------------------------------------------------------

def process_table_right(
    table_file: Path,
    desired_compounds: set[str],
    not_processed_path: Path
) -> str:
    """
    Process a CSV *table_file* aligning numeric columns to the right edge.
    Steps:
      1. Read all rows and identify the first numeric column per row.
      2. Pad rows so that numeric data aligns at a common right offset.
      3. Write the adjusted rows back to CSV.
      4. Load into pandas DataFrame, transpose, and locate header row by searching
         for any desired compound keywords.
      5. Extract data beneath the header, assign new columns, add an 'IDS' column.
      6. If within a 'splitted' folder, save under 'dataframe/right', else move to
         unprocessed directory.
    Returns one of:
      'processed', 'header_miss', 'max_arg_empty', or 'exception'.
    """
    try:
        # Read raw CSV and compute shifting parameters
        with table_file.open('r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
        max_columns = max(len(row) for row in rows)
        rows_info = []
        max_first_numeric_idx = 0
        for row in rows:
            first_numeric_idx = None
            for idx, val in enumerate(row):
                val_strip = val.strip()
                if val_strip in ('', '-', ' '):
                    continue
                if is_numeric(val_strip):
                    first_numeric_idx = idx
                    break
            if first_numeric_idx is None:
                first_numeric_idx = len(row)
            max_first_numeric_idx = max(max_first_numeric_idx, first_numeric_idx)
            rows_info.append({'row': row, 'first_numeric_idx': first_numeric_idx})

        # Align numeric data to the right by padding
        adjusted_rows = []
        for info in rows_info:
            row = info['row']
            shift = max_first_numeric_idx - info['first_numeric_idx']
            if shift > 0:
                row = row + ['-'] * shift
            row += ['-'] * (max_columns - len(row))
            adjusted_rows.append(row)

        # Overwrite CSV with aligned data
        with table_file.open('w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(adjusted_rows)

        # Load into DataFrame and drop empty columns
        df = pd.read_csv(table_file, encoding='utf-8', header=None).dropna(axis=1, how='all').T
       
        # Identify header row by presence of desired compounds
        header_idx = next(
            (i for i, row in enumerate(df.values)
             if any(normalize_string(str(h)) in desired_compounds for h in row)),
            None
        )

        if header_idx is not None:
            new_header = df.iloc[header_idx]
            new_df = df.iloc[header_idx + 1:].copy()
            new_df.columns = new_header
            new_df['IDS'] = str(table_file)

            # Save processed file under 'dataframe/right'
            if "splitted" in table_file.parts:
                output_path = table_file.parents[1] / "dataframe" / "right"
                output_path.mkdir(parents=True, exist_ok=True)
                new_df.to_csv(output_path / (table_file.stem + ".csv"), index=False)
                return 'processed'
            else:
                copy_to_not_processed(table_file, not_processed_path)
                return 'header_miss'
        else:
            copy_to_not_processed(table_file, not_processed_path)
            return 'header_miss'

    except ValueError as e:
        # Handle empty-rows scenario specifically
        if "max() iterable argument is empty" in str(e):
            copy_to_not_processed(table_file, not_processed_path)
            return 'max_arg_empty'
        else:
            copy_to_not_processed(table_file, not_processed_path)
            return 'exception'
    except Exception:
        copy_to_not_processed(table_file, not_processed_path)
        return 'exception'

# ------------------------------------------------------------------------------
# 4. LEFT-Edge Table Processing Logic
# ------------------------------------------------------------------------------

def process_table_left(
    table_file: Path,
    desired_compounds: set[str],
    not_processed_path: Path
) -> str:
    """
    Process a CSV *table_file* aligning numeric columns to the left edge.
    Steps mirror the RIGHT logic but pad to align at a common left offset.
    Returns one of:
      'processed', 'header_miss', 'max_arg_empty', or 'exception'.
    """
    try:
        # Read raw CSV rows
        with table_file.open('r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        rows_info = []
        max_left_gap = 0
        for row in rows:
            shift_left_count = 0
            first_numeric_idx = None
            for idx, cell in enumerate(row):
                cell_strip = cell.strip()
                if cell_strip in ('', '-', ' '):
                    shift_left_count += 1
                elif is_numeric(cell_strip):
                    first_numeric_idx = idx
                    break
            if first_numeric_idx is None:
                first_numeric_idx = len(row)
            max_left_gap = max(max_left_gap, shift_left_count)
            rows_info.append({'row': row, 'first_numeric_idx': first_numeric_idx, 'shift_left_count': shift_left_count})

        # Pad rows to align numeric data to the left offset
        adjusted_rows = []
        for info in rows_info:
            row = info['row']
            f_idx = info['first_numeric_idx']
            left_count = info['shift_left_count']
            if left_count < max_left_gap:
                diff = max_left_gap - left_count
                row = row[:f_idx] + ['-'] * diff + row[f_idx:]
            adjusted_rows.append(row)

        # Ensure all rows have equal length by padding end gaps
        max_total_columns = max(len(r) for r in adjusted_rows)
        final_rows = []
        for r in adjusted_rows:
            final_rows.append(r + ['-'] * (max_total_columns - len(r)))

        # Overwrite CSV with aligned data
        with table_file.open('w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(final_rows)

        # Load, transpose and drop empty columns in DataFrame
        df = pd.read_csv(table_file, encoding='utf-8', header=None).dropna(axis=1, how='all').T

        header_idx = next(
            (i for i, row in enumerate(df.values)
             if any(normalize_string(str(h)) in desired_compounds for h in row)),
            None
        )

        # Identify header row containing desired compounds
        if header_idx is not None:
            new_header = df.iloc[header_idx]
            new_df = df.iloc[header_idx + 1:].copy()
            new_df.columns = new_header
            new_df['IDS'] = str(table_file)

            # Save processed file under 'dataframe/left'
            output_path = table_file.parents[1] / "dataframe" / "left"
            output_path.mkdir(parents=True, exist_ok=True)
            new_df.to_csv(output_path / (table_file.stem + ".csv"), index=False)
            return 'processed'
        else:
            copy_to_not_processed(table_file, not_processed_path)
            return 'header_miss'

    except ValueError as e:
        # Handle empty-rows scenario specifically
        if "max() iterable argument is empty" in str(e):
            copy_to_not_processed(table_file, not_processed_path)
            return 'max_arg_empty'
        else:
            copy_to_not_processed(table_file, not_processed_path)
            return 'exception'
    except Exception:
        copy_to_not_processed(table_file, not_processed_path)
        return 'exception'

# ------------------------------------------------------------------------------
# 5. Main Execution Flow and Summary Reporting
# -----------------------------------------------------------------------------

def main():
    """
    Iterate over all split CSV tables and apply both RIGHT and LEFT processing.
    Collect status counts and print a summary report for each method.
    """
    from collections import Counter

    counters_right = Counter()
    counters_left = Counter()

    # Process every CSV under 'processed/splitted'
    for table_file in a_input_path.rglob("processed/splitted/*.csv"):
        status_r = process_table_right(table_file, desired_compounds, not_processed_path)
        counters_right[status_r] += 1

        status_l = process_table_left(table_file, desired_compounds, not_processed_path)
        counters_left[status_l] += 1

    # Report RIGHT results
    not_processed_right = (
        counters_right.get('header_miss', 0) +
        counters_right.get('exception', 0) +
        counters_right.get('max_arg_empty', 0)
    )
    print("\nProcessing Summary (RIGHT):")
    print(f"  Processed and saved: {counters_right.get('processed', 0)}")
    print(f"  Not processed: {not_processed_right}")
    print("  Reasons:")
    print(f"    - Missing header or no desired compounds: {counters_right.get('header_miss', 0)}")
    print(f"    - Execution errors: {counters_right.get('exception', 0)}")
    print(f"    - Empty tables: {counters_right.get('max_arg_empty', 0)}")

    # Report LEFT results
    not_processed_left = (
        counters_left.get('header_miss', 0) +
        counters_left.get('exception', 0) +
        counters_left.get('max_arg_empty', 0)
    )
    print("\nProcessing Summary (LEFT):")
    print(f"  Processed and saved: {counters_left.get('processed', 0)}")
    print(f"  Not processed: {not_processed_left}")
    print("  Reasons:")
    print(f"    - Missing header or no desired compounds: {counters_left.get('header_miss', 0)}")
    print(f"    - Execution errors: {counters_left.get('exception', 0)}")
    print(f"    - Empty tables: {counters_left.get('max_arg_empty', 0)}")

    print("Operation completed successfully.")

if __name__ == "__main__":
    main()
