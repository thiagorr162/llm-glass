import json
import pandas as pd
from pathlib import Path  
import re

base_path = Path("data/raw")

csv_path1 = base_path / "final_filtered_concatenated.csv"
csv_path2 = base_path / "refractiveIndex.csv"
csv_path3 = base_path / "merged_df.csv"
dataframe1 = pd.read_csv(csv_path1, low_memory=False)
dataframe2 = pd.read_csv(csv_path2, low_memory=False)
dataframe3 = pd.read_csv(csv_path3, low_memory=False)
dataframe4 = pd.concat([dataframe1, dataframe3], axis=1).drop_duplicates()
json_path =  Path("json/properties.json")

with open(json_path, 'r') as file:
    data = json.load(file)

def Filter_By_Compounds(dataframe):
    """
    Returns
    - Filtered DataFrame with desired compounds.
    - Excluded DataFrame with columns not in the desired compounds list.
    """
    desired_compounds = data["desired_compounds"]
    filtered_columns = [col for col in dataframe.columns if col in desired_compounds]
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

def Filter_by_have_numbers(dataframe):
    """
    Returns:
    - Filtered DataFrame with columns containing numbers.
    - Excluded DataFrame with columns that do not contain numbers.
    """
    filtered_columns = [col for col in dataframe.columns if re.search(r'\d+', col)]
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

def Filter_by_2to8(dataframe):
    """
    Returns:
    - Filtered DataFrame with columns that have names between 2 and 8 characters.
    - Excluded DataFrame with columns that do not match this length criteria.
    """
    filtered_columns = [col for col in dataframe.columns if 2 <= len(col) <= 8]
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

def Pull_Apart_Compoundsdataframe_NotCompoundsdataframe(dataframe):
    """
    Returns:
    - Filtered DataFrame with columns that meet compound criteria (numbers present, 2-8 characters).
    - Excluded DataFrame with columns that do not meet the criteria.
    """
    dataframe_with_numbers, _ = Filter_by_have_numbers(dataframe)
    dataframe_with_compounds, _ = Filter_by_2to8(dataframe_with_numbers)
    excluded_columns = dataframe.columns.difference(dataframe_with_compounds.columns)
    return dataframe_with_compounds, dataframe[excluded_columns]

def Filter_by_not_plus(dataframe):
    """
    Returns:
    - Filtered DataFrame with columns that do not contain the '+' character.
    - Excluded DataFrame with columns that contain the '+' character.
    """
    filtered_columns = [col for col in dataframe.columns if "+" not in col]
    excluded_columns = [col for col in dataframe.columns if "+" in col]
    return dataframe[filtered_columns], dataframe[excluded_columns]

def insert_zeros(dataframe):
    """
    Cleans the DataFrame by replacing '—' and NaN with 0.
    """
    dataframe = dataframe.replace('—', 0).fillna(0)
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

def remove_empty_columns(dataframe):
    """
    Returns:
    - Filtered DataFrame without columns that contain only zeros.
    - Excluded DataFrame with columns that contain only zeros.
    """
    empty_columns = dataframe.columns[(dataframe == 0).all()]
    excluded_columns_df = dataframe[empty_columns]
    filtered_dataframe = dataframe.drop(columns=empty_columns)
    return filtered_dataframe, excluded_columns_df

def sum_lines(dataframe, tolerance=2):
    """
    Returns:
    - Filtered DataFrame with rows whose sum is close to 100.
    - Excluded DataFrame with rows whose sum is not within the tolerance range of 100.
    """
    columns = dataframe.columns
    row_sums = dataframe[columns].sum(axis=1)
    rows_with_sum_100 = dataframe[(row_sums >= 100 - tolerance) & (row_sums <= 100 + tolerance)]
    excluded_rows = dataframe.drop(rows_with_sum_100.index)
    return rows_with_sum_100, excluded_rows

def filter_by_properties(dataframe):
    """
    Returns:
    - Filtered DataFrame with columns containing specified properties.
    - Excluded DataFrame with columns that do not contain specified properties.
    """
    properties = ["refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", "devitrification",
                  "point", "crystallization", "thermal", "mean", "glass transition", "crystallinity", "electric",
                  "onset", "transition", "permittivity", "iso"]
    filtered_columns = [col for col in dataframe.columns if any(prop.lower() in col.lower() for prop in properties)]
    filtered_dataframe = dataframe[filtered_columns]
    excluded_dataframe = dataframe.drop(columns=filtered_columns)
    return filtered_dataframe, excluded_dataframe

def remove_rows_with_na(dataframe):
    """"
    Returns:
    - Filtered DataFrame without any rows that contain at least 1 NaN
    - Excluded DataFrame with any rows that contain at least 1 NaN
    """
    filtered_df = dataframe.dropna()
    excluded_df = dataframe.loc[dataframe.isna().any(axis=1)]
    return filtered_df, excluded_df

def all_filters(dataframe):
    """
    Returns:
    - Filtered DataFrame with rows summing to 100 and columns of specified properties.
    - Excluded DataFrame with rows not meeting the criteria.
    """
    dataframe = insert_zeros(dataframe)
    dataframe, excluded_by_removeemptycolumns= remove_empty_columns(dataframe)
    filtered_dataframe, _ = Filter_By_Compounds(dataframe)
    rows_with_sum_100, excluded_by_sumlines = sum_lines(filtered_dataframe)
    properties_df, _ = filter_by_properties(dataframe)
    final_filtered_withplus_and_na = pd.concat([rows_with_sum_100, properties_df], axis=1)
    final_filtered_withna, excluded_by_filterbynotplus = Filter_by_not_plus(final_filtered_withplus_and_na)
    final_filtered, excluded_by_removerowswithna= remove_rows_with_na(final_filtered_withna)
    return final_filtered, excluded_by_removeemptycolumns, excluded_by_sumlines, excluded_by_filterbynotplus, excluded_by_removerowswithna

final_filtered, excluded_by_removeemptycolumns, excluded_by_sumlines, excluded_by_filterbynotplus, excluded_by_removerowswithna = all_filters(dataframe4)

# imprimindo o tamanho da tabela final  e das tabelas excluidas

filtered_path = Path("filter_table/filtered")

final_filtered.to_csv                 (filtered_path / 'final_df.csv',                       index = False)
excluded_by_removeemptycolumns.to_csv (filtered_path / 'excluded_by_removeemptycolumns.csv', index = False)
excluded_by_sumlines.to_csv           (filtered_path / 'excluded_by_sumlines.csv',           index = False)
excluded_by_filterbynotplus.to_csv    (filtered_path / 'excluded_by_filterbynotplus.csv',    index = False)
excluded_by_removerowswithna.to_csv   (filtered_path / 'excluded_by_removerowswithna.csv',   index = False)

print(f"Tamanho do dataframe original: {dataframe4.shape}")
print(f"Tamanho da tabela final: {final_filtered.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro que remove colunas vazias: {excluded_by_removeemptycolumns.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro da soma das linhas: {excluded_by_sumlines.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro de ter + no nome da col: {excluded_by_filterbynotplus.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro de remover linhas com NaN: {excluded_by_removerowswithna.shape}")
