import pathlib
import pandas as pd

# Input and output paths
input_path = pathlib.Path("data/patents")
output_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")  # This file is not used here but kept as in the original.

def merge_csv_files(input_folder, output_file):
    """
    Merges all CSV files from a directory into a single DataFrame and saves it to disk.

    Args:
        input_folder (pathlib.Path): Path to the folder containing the CSVs.
        output_file (pathlib.Path): Path to the output file.
    """
    all_dfs = []
    for table_file in input_folder.rglob("*/processed/dataframe/*.csv"):
        try:
            df = pd.read_csv(table_file)
            all_dfs.append(df)
        except Exception as e:
            print(f"Error reading file {table_file}: {e}")

    if not all_dfs:
        print("No CSV files found to merge.")
        return

    try:
        merged_df = pd.concat(all_dfs, join="outer", ignore_index=True)
        merged_df.to_csv(output_file, index=False)
        print(f"Merged DataFrame saved to: {output_file}")
        print("Generated DataFrame size:", merged_df.shape)
    except Exception as e:
        print(f"Error merging or saving CSV files: {e}")

# Execute the merge function
merge_csv_files(input_path, output_path / "merged_df.csv")
print("Operation completed successfully.")
