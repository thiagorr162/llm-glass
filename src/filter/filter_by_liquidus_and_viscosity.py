import pandas as pd
import json
import re

# Load final_df
final_df = pd.read_csv("data/filtered/final_df.csv")

# Load desired_compounds from the same JSON file as before
with open("json/properties.json", 'r') as file:
    data = json.load(file)
desired_compounds = data.get("desired_compounds", [])

print(f"Desired Compounds ({len(desired_compounds)}): {desired_compounds}")

viscosity_patterns = [
        r'\bviscosity\b',
        r'η',
        r'\bmu\b',
        r'µ',
        r'\bvisc(?:osity)?\b',
        r'\blogη\b',
        r'\bvisc\.\b',
        r'\bvisc at\b',
        r'\bliquidus viscosity\b',
        r'\bviscosity at\b',
        r'\bηliq\b',
        r'\blogη(?:tl|tp)\b',
        r'\bη(?:liquidus|liq)?\b',
        r'\bviscosity \(?:liquidus\)',
        r'\bviscosity\s*at\s*liquidus\b',
        r'\bviscosity liquidus\b',
    ]
liquidus_patterns = [
        r'\bliquidus\b',
        r'\bliq(?:uidus)?\b',
        r'\btliquidus\b',
        r'\btliq\b',
        r'\bt\s*\(liquidus\)',
        r'\btl\b',
        r'\bliquid phase\b',
        r'\bliquidus temp(?:erature)?\b',
        r'\bliquidus internal\b',
        r'\bliquidus temp\b',
        r'\bliquidus temperature\b',
        r'\bt\s*\(liq(?:uidus)?\)',
        r'\bliquidus temperature t1\b',
        r'\bliquidus temperature lt\b',
        r'\bliquidus temperature tl\b',
        r'\bliquidus temp\s*\(lt\)\b',
        r'\bliquidus temp\s*\(tl\)\b',
        r'\bliquidus temperature [tT][lL]\b',
        r'\bliquidus temperature [tT]log\b',
        r'\bt\s*log\b',
    ]
    
is_liquidus = any(re.search(pat, lower_name) for pat in liquidus_patterns)
is_viscosity = any(re.search(pat, lower_name) for pat in viscosity_patterns)
    
def is_viscosity_column(col_name: str) -> bool:
    """
    Determines if a column name is related to the Viscosity property.
    Excludes columns that also indicate Liquidus properties.
    """
    lower_name = col_name.lower()

    is_viscosity = any(re.search(pat, lower_name) for pat in viscosity_patterns)
    is_liquidus = any(re.search(pat, lower_name) for pat in liquidus_patterns)
    
    # Exclude columns that are both Viscosity and Liquidus
    if is_viscosity and is_liquidus:
        return False
    return is_viscosity

def identify_liq_visc_pairs(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Liq-Visc-Paired' column indicating whether a row has at least one non-zero liquidus
    and one non-zero viscosity value.
    """
    liquidus_cols = [col for col in dataframe.columns if is_liquidus_column(col)]
    viscosity_cols = [col for col in dataframe.columns if is_viscosity_column(col)]
    
    print(f"Identified Liquidus Columns ({len(liquidus_cols)}): {liquidus_cols}")
    print(f"Identified Viscosity Columns ({len(viscosity_cols)}): {viscosity_cols}")
    
    if not liquidus_cols or not viscosity_cols:
        dataframe["Liq-Visc-Paired"] = 0
        return dataframe
    
    has_liquidus = (dataframe[liquidus_cols] != 0).any(axis=1)
    has_viscosity = (dataframe[viscosity_cols] != 0).any(axis=1)
    
    dataframe["Liq-Visc-Paired"] = (has_liquidus & has_viscosity).astype(int)
    return dataframe

def remover_linhas_0_liq_visc(dataframe: pd.DataFrame, liquidus_cols: list, viscosity_cols: list) -> pd.DataFrame:
    """
    Removes rows where all values across both liquidus and viscosity columns are zero.
    
    Parameters
    ----------
    dataframe : pd.DataFrame
        The input DataFrame.
    liquidus_cols : list
        List of liquidus column names.
    viscosity_cols : list
        List of viscosity column names.
    
    Returns
    -------
    pd.DataFrame
        The filtered DataFrame.
    """
    liq_visc_cols = liquidus_cols + viscosity_cols
    if not liq_visc_cols:
        print("No liquidus or viscosity columns found. Returning original DataFrame.")
        return dataframe.copy()
    
    # Create a boolean Series where True indicates the row has all zeros in liquidus and viscosity columns
    all_zeros = (dataframe[liq_visc_cols] == 0).all(axis=1)
    
    # Exclude these rows
    filtered_df = dataframe[~all_zeros].copy()
    
    return filtered_df

def count_non_zero_rows(dataframe: pd.DataFrame, liquidus_cols: list, viscosity_cols: list) -> tuple:
    """
    Counts the number of rows that have at least one non-zero value in liquidus columns
    and the number of rows that have at least one non-zero value in viscosity columns.
    
    Parameters
    ----------
    dataframe : pd.DataFrame
        The input DataFrame.
    liquidus_cols : list
        List of liquidus column names.
    viscosity_cols : list
        List of viscosity column names.
    
    Returns
    -------
    tuple
        A tuple containing two integers:
        - Number of rows with at least one non-zero liquidus value.
        - Number of rows with at least one non-zero viscosity value.
    """
    if liquidus_cols:
        rows_with_liquidus_data = (dataframe[liquidus_cols] != 0).any(axis=1).sum()
    else:
        rows_with_liquidus_data = 0
    
    if viscosity_cols:
        rows_with_viscosity_data = (dataframe[viscosity_cols] != 0).any(axis=1).sum()
    else:
        rows_with_viscosity_data = 0
    
    return rows_with_liquidus_data, rows_with_viscosity_data

# 1. Extract only compound columns from final_df
compounds_only = final_df[[col for col in final_df.columns if col in desired_compounds]]

# 2. Identify liquidus and viscosity columns in final_df
liquidus_cols = [col for col in final_df.columns if is_liquidus_column(col)]
viscosity_cols = [col for col in final_df.columns if is_viscosity_column(col)]

print(f"Liquidus Columns Identified: {liquidus_cols}")
print(f"Viscosity Columns Identified: {viscosity_cols}")

# 3. Apply the pairing function to add "Liq-Visc-Paired" column
final_df = identify_liq_visc_pairs(final_df)

# 4. **Exclude rows where all liquidus and viscosity columns are zero**
filtered_df = remover_linhas_0_liq_visc(final_df, liquidus_cols, viscosity_cols)

# 5. **Count rows with at least one non-zero liquidus and viscosity data**
rows_with_liquidus_data, rows_with_viscosity_data = count_non_zero_rows(filtered_df, liquidus_cols, viscosity_cols)

print(f"Number of rows with at least one liquidus data: {rows_with_liquidus_data}")
print(f"Number of rows with at least one viscosity data: {rows_with_viscosity_data}")

# 6. **Construct selected_columns safely (using the filtered_df now)**
selected_columns = [col for col in desired_compounds + liquidus_cols + viscosity_cols + ["Liq-Visc-Paired", "IDS"] if col in filtered_df.columns]

# Identify missing compounds in the filtered DataFrame
missing_compounds = [comp for comp in desired_compounds if comp not in filtered_df.columns]

if missing_compounds:
    print("Warning: The following desired compounds are missing from filtered_df:")
    for comp in missing_compounds:
        print(f" - {comp}")
else:
    print("All desired compounds are present in filtered_df.")

# 7. **Create the new DataFrame with existing columns**
compounds_liquidus_and_viscosity_only_df = filtered_df[selected_columns]

# 8. **Save the resulting DataFrame**
compounds_liquidus_and_viscosity_only_df.to_csv("data/filtered/compounds_liquidus_and_viscosity_only_df.csv", index=False)

print("compounds_liquidus_and_viscosity_only_df created successfully!")
