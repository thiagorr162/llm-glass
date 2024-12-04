# Data Filtering and Analysis Project

This repository contains a set of Python functions designed to filter and analyze chemical compound data and associated properties. The code is developed to process a CSV file, apply custom filters, and generate a final DataFrame with relevant information.

## Requirements

Before you begin, ensure you have the following installed:

- **Python 3.x**
- **Python Libraries**:
  - `pandas`
  - `json`
  - `re`
  - `pathlib`

## Function Descriptions

The code contains several functions that apply filters to chemical compound data and properties. Below is a detailed description of each function:

### 1. `filter_by_compounds(dataframe)`

Filters the DataFrame columns based on the compounds defined in the `properties.json` file. Only columns that match the desired compounds are retained.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Filtered DataFrame**: Contains only the columns corresponding to the desired compounds as specified in `properties.json`.
- **Excluded DataFrame**: Contains the columns that do not match the desired compounds.

### 2. `filter_columns_without_plus(dataframe)`

Removes columns that contain the `'+'` character in their names. This is useful when you want to exclude columns with a specific pattern in their names.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Filtered DataFrame**: Contains only the columns without the `'+'` character in their names.
- **Excluded DataFrame**: Contains the columns that have the `'+'` character.

### 3. `clean_and_fill_zeros(dataframe)`

Replaces `'—'` (em dashes) and `NaN` (Not a Number) values with `0` in the DataFrame. This helps to clean the DataFrame, making the data more consistent and ready for analysis.

**Parameters:**

- `dataframe`: DataFrame containing the data to be cleaned.

**Returns:**

- **Cleaned DataFrame**: All `'—'` and `NaN` values are replaced with `0`, and data types are converted to numeric.

### 4. `remove_columns_with_only_zeros(dataframe)`

Removes columns from the DataFrame that contain only zero values. Empty columns can be removed to improve analysis performance and make the DataFrame more concise.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Filtered DataFrame**: DataFrame without columns that are entirely zeros.
- **Excluded DataFrame**: Contains the columns that were removed because they were empty.

### 5. `filter_rows_by_sum(dataframe, tolerance=2)`

Filters the DataFrame rows where the sum of the column values is close to 100, within a defined tolerance (default is 2). This filter can be useful to adjust the data and ensure that the values sum to an expected value (e.g., in material compositions).

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.
- `tolerance` (optional): Margin of error for the sum; default is `2`.

**Returns:**

- **Filtered DataFrame**: Contains rows where the sum is approximately 100%.
- **Excluded DataFrame**: Contains rows that do not meet the sum criteria.

### 6. `filter_columns_by_properties(dataframe)`

Filters the DataFrame columns that contain specific chemical or physical properties, such as "refractive", "density", "abbe", etc. These properties are defined in a fixed list and are searched for in the column names.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Filtered DataFrame**: Contains only the columns with the specified properties.
- **Excluded DataFrame**: Contains the columns that do not have the desired properties.

### 7. `remove_rows_with_nan(dataframe)`

Removes rows that contain `NaN` values. This should be applied at the end of the filtering process.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Filtered DataFrame**: Contains only the rows without `NaN` values.
- **Excluded DataFrame**: Contains the rows that were removed due to `NaN` values.

### 8. `merge_refractive_index_columns(dataframe)`

Merges multiple refractive index columns into a single column. This is useful when you have multiple columns representing the same property and want to consolidate them.

**Parameters:**

- `dataframe`: DataFrame containing the data to be processed.

**Returns:**

- **Merged DataFrame**: DataFrame with refractive index columns merged into one.
- **Refractive Only DataFrame**: Contains only the refractive index columns and relevant data.

### 9. `remover_linhas_0(dataframe)`

Removes rows where the sum of the values equals zero. This helps to eliminate rows that do not contribute meaningful data.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Non-null Rows DataFrame**: Contains only the rows where the sum is not zero.
- **Null Rows DataFrame**: Contains the rows where the sum equals zero.

### 10. `apply_all_filters(dataframe)`

This is the main function that applies all the previously defined filters in sequence. It normalizes the data, applies filters for compounds, properties, sum of rows, and removes empty columns, retaining only data relevant for final analysis.

**Parameters:**

- `dataframe`: DataFrame containing the data to be filtered.

**Returns:**

- **Final Filtered DataFrame**: Contains only the columns and rows that meet all criteria (desired compounds, properties, and sum of rows close to 100).
- **Excluded DataFrames**:
  - `excluded_empty`: Columns removed for being entirely empty.
  - `excluded_sum`: Rows removed due to the sum being outside the range.
  - `excluded_plus`: Columns removed because they contain the `'+'` character.
  - `excluded_nan`: Rows removed due to `NaN` values.
- **Additional DataFrames**:
  - `refractive_only`: DataFrame containing compounds and refractive indices only.
  - `dataframe_compounds_without_properties`: Compounds without associated properties.

## Usage

1. Ensure you have the following directory structure:

   ```
   data/
     patents/
       merged_df.csv
     filtered/
   json/
     properties.json
   ```

2. Place your `merged_df.csv` file inside `data/patents/` and `properties.json` inside `json/`. The `properties.json` file should contain a key `"desired_compounds"` with a list of the compounds you wish to filter.

3. Run the script:

   ```bash
   python script_name.py
   ```

4. Processed files will be saved in `data/filtered/`.

## Output Files

Saved in `data/filtered/`:

- `final_df.csv`: Final filtered DataFrame after all filters have been applied.
- `excluded_by_removeemptycolumns.csv`: Columns removed because they were entirely zeros.
- `excluded_by_sumlines.csv`: Rows removed because their sums did not meet the criteria.
- `excluded_by_filterbynotplus.csv`: Columns removed because they contained the `'+'` character.
- `excluded_by_removerowswithna.csv`: Rows removed due to containing `NaN` values.
- `compounds_and_refractive_only_df.csv`: DataFrame containing compounds and refractive indices only.
- `dataframe_compounds_without_properties.csv`: Compounds without associated properties.

## Processing Summary

The script provides a summary of the data processing steps, displaying the sizes of the original and resulting DataFrames.

---

By following this guide, you should be able to filter and analyze your chemical compound data effectively using the provided functions.
