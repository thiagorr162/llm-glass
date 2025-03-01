# Data Filtering and Analysis Project

This repository contains three main Python scripts, each designed to filter and process chemical compound data (stored in CSV format) based on various properties or criteria. These scripts work alongside a JSON file (`properties.json`) that defines the **desired compounds** and other parameters.

---

## 1. `filters.py`
**What it does**:  
- **`filters.py`** is a robust, all-in-one filtering script. It applies multiple filtering steps—removing empty columns, filtering rows by sum, isolating desired compounds, merging refractive index columns, etc.—in a single pipeline.  
- **Pro**: Comprehensive (handles everything in one pass).  
- **Con**: Slower due to its exhaustive approach.

**When to use**:  
- If you need a **single, unified** solution that processes and cleans the data thoroughly in **one go**, `filters.py` is suitable.  

---

## 2. `filter_by_properties_0.1.py`
**What it does**:  
- **`filter_by_properties_0.1`** specifically focuses on gathering and cleaning all relevant properties from the raw CSV file.  
- It filters out irrelevant columns, handles rows by sum tolerance, deals with columns containing “+” signs (except for valid refractive index columns), and finally outputs a `final_df.csv` with the cleaned and consolidated properties.

**When to use**:  
- **First**: If you prefer a **modular approach**, run `filter_by_properties_0.1` **before** applying specific property merges (such as refractive index).  
- It creates a **clean, property-rich DataFrame** (`final_df.csv`) that other scripts can further refine.

---

## 3. `filter_by_RI_0.1.py`
**What it does**:  
- **`filter_by_RI_0.1`** takes the output (`final_df.csv`) from `filter_by_properties_0.1` and specifically merges columns related to **Refractive Index (RI)** into a single column.  
- It identifies possible RI columns using keywords/patterns, then sums them per row. If more than one RI column has data for the same row, it flags the merged value as `-1` to indicate ambiguity.

**When to use**:  
- **Second**: After you have a cleaned DataFrame (`final_df.csv`), use `filter_by_RI_0.1` to unify refractive index data and generate a final file (`final_df_atualizado.csv`).

---

## Directory Structure

A typical directory layout looks like this:

```
data/
 ┣ patents/
 ┃   ┗ merged_df.csv   <- Your raw data file
 ┣ filtered/           <- Filtered data outputs go here
json/
 ┗ properties.json     <- File that contains "desired_compounds" and possibly other parameters
```

Make sure:
- **`merged_df.csv`** is inside **`data/patents/`**.  
- **`properties.json`** is inside **`json/`** and contains the key `"desired_compounds"` among other configurations.

---

## Usage Instructions

1. **Modular Approach** (two-step):

   - **Step 1**: Run `filter_by_properties_0.1.py`  
     - This script will read `merged_df.csv`, apply general cleaning and property-based filtering, and produce **`final_df.csv`** in `data/filtered/`.
   - **Step 2**: Run `filter_by_RI_0.1.py`  
     - This script will read **`final_df.csv`** from the `data/filtered/` folder and merge any refractive index columns into one. It then saves **`final_df_atualizado.csv`** in the same folder.

2. **Single Pass**:
   - Run `filters.py` by itself if you want a **robust, all-in-one** process. This will output a fully filtered CSV (named similarly to `final_df_dated.csv`) and optional intermediate files.

---

## Requirements

Before running these scripts, ensure you have the following:

- **Python 3.x**
- **Libraries**:
  - `pandas`
  - `json`
  - `re`
  - `pathlib`

Install missing libraries using:
```bash
pip install pandas
```
*(The others are standard libraries in most Python distributions.)*

---

## Output Files

- **`final_df.csv`** (from `filter_by_properties_0.1`):  
  Cleaned and consolidated DataFrame with all relevant properties.

- **`final_df_atualizado.csv`** (from `filter_by_RI_0.1`):  
  Final DataFrame with refractive index columns merged.

- **Various “excluded_*.csv” files** and **“compounds_and_refractive_only_df.csv”** (optional in some scripts)  
  Intermediate or specialized DataFrames detailing what was filtered out or focusing on specific subsets (e.g., only compounds and refractive indices).

---

## Notes

- Always check that your **`properties.json`** file is correct. The scripts rely on the `"desired_compounds"` and other property keywords to match columns in the CSV.  
- The **summaries** printed at the end of each script help you track how many rows/columns were removed or retained at each filter step.  
- Use `filters.py` if you need a **single** robust (but slower) solution; otherwise, use `filter_by_properties_0.1` followed by `filter_by_RI_0.1` for a more **modular** approach.

---

By following these instructions, you can filter and analyze your chemical compound data to retain only relevant properties, unify refractive index columns, and produce clean, concise CSV outputs for further research and analysis.
