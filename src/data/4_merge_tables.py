import pathlib
import pandas as pd


# ------------------------------------------------------------------------------
# 1. Path Configuration
# ------------------------------------------------------------------------------

# Define base directory containing all patent folders
base_path   = pathlib.Path("data/patents")
# Set output directory where merged CSVs will be saved (same as base_path)
output_path = base_path  


# ------------------------------------------------------------------------------
# 2. Function: merge_side
# ------------------------------------------------------------------------------

def merge_side(side: str):
    """
    Merge all CSV files from the specified 'side' subdirectory into a single DataFrame,
    then save as a consolidated CSV named:
      {SIDE}_Merged_df({rows}x{cols}).csv

    Steps:
      1. Construct recursive glob pattern:
         data/patents/**/processed/dataframe/{side}/*.csv
      2. Iterate over matching files, reading each into a pandas DataFrame.
      3. Concatenate all DataFrames with outer join, resetting the index.
      4. Determine the shape (rows, cols) of the merged DataFrame.
      5. Write the merged DataFrame to CSV in the output_path.
    """
    # Build file search pattern for the given side
    pattern = f"processed/dataframe/{side}/*.csv"
    all_dfs = []
    
    # Recursively search through all patent directories
    for csv_file in base_path.rglob(pattern):
        try:
            df = pd.read_csv(csv_file)
            all_dfs.append(df)
        except Exception as e:
            # Log any file read errors without interrupting the loop
            print(f"Error reading {csv_file}: {e}")
    
    # If no files were found, notify and exit
    if not all_dfs:
        print(f"No CSV files found for '{side}'.")
        return

    # Concatenate DataFrames, preserving all columns and resetting index
    merged_df = pd.concat(all_dfs, join="outer", ignore_index=True)
    rows, cols = merged_df.shape
    # Construct output filename with uppercase side and DataFrame shape
    filename = f"{side.upper()}_Merged_df({rows}x{cols}).csv"
    out_file = output_path / filename
    
    try:
        # Save merged DataFrame to CSV without writing row indices
        merged_df.to_csv(out_file, index=False)
        print(f"[{side.upper()}] saved to {out_file} — shape {rows}x{cols}")
    except Exception as e:
        # Log any write errors
        print(f"Error saving {filename}: {e}")

# ------------------------------------------------------------------------------
# 3. Main Execution Flow
# ------------------------------------------------------------------------------

def main():
    """
    Execute merge_side for both 'left' and 'right' directories,
    then print a completion message.
    """
    merge_side("left")
    merge_side("right")
    print("Operation completed successfully.")

if __name__ == "__main__":
    main()
