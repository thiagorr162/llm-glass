import json
import pandas as pd
from pathlib import Path  
import re

# Define base paths
BASE_PATH = Path("data/patents")
FILTERED_PATH = Path("data/filtered")

# Load data
csv_path = BASE_PATH / "merged_df.csv"
dataframe_t = pd.read_csv(csv_path, low_memory=False)
json_path = Path("json/properties.json")
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
    Adjusts DataFrame rows so that rows summing to approximately 1 are scaled up to sum to approximately 100.
    
    Parameters:
    - dataframe: pandas DataFrame containing numerical data.
    - tolerance: numerical value representing the acceptable deviation from the target sums (default is 2).
    
    Returns:
    - rows_with_sum_100: DataFrame with rows summing close to 100, including those scaled from sum of 1.
    - excluded_rows: DataFrame with rows whose sums are not within the tolerance ranges of 100 or 1.
    """
    columns = dataframe.columns
    row_sums = dataframe[columns].sum(axis=1)
    
    # Tolerance for sum of 100
    tolerance_100 = tolerance
    # Tolerance for sum of 1 (proportional to tolerance for 100)
    tolerance_1 = tolerance / 100
    
    # Identify rows where the sum is close to 100
    mask_sum_100 = (row_sums >= 100 - tolerance_100) & (row_sums <= 100 + tolerance_100)
    rows_that_sum_100 = dataframe.loc[mask_sum_100]
    
    # Identify rows where the sum is close to 1
    mask_sum_1 = (row_sums >= 1 - tolerance_1) & (row_sums <= 1 + tolerance_1)
    rows_with_sum_1 = dataframe.loc[mask_sum_1]
    
    # Scale rows summing close to 1 by 100
    rows_with_sum_1_scaled = rows_with_sum_1 * 100
    # Combine the rows summing to 100 and the scaled rows
    rows_with_sum_100 = pd.concat([rows_that_sum_100, rows_with_sum_1_scaled])

    # Exclude rows not included in the rows_with_sum_100
    included_indices = rows_with_sum_100.index
    excluded_rows = dataframe.drop(index=included_indices)

    return rows_with_sum_100, excluded_rows

def filter_by_properties(dataframe):
    """
    Returns:
    - Filtered DataFrame with columns containing specified properties.
    - Excluded DataFrame with columns that do not contain specified properties.
    """
    properties = ["refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", "devitrification",
                  "point", "crystallization", "thermal", "mean", "glass transition", "crystallinity", "electric",
                  "onset", "transition", "permittivity", "iso", "RI", "index", "ref", "nd", "η", "nm", "ratio", "n5", "n6", "n7", "n8", "n9"]
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

def merge_refractive_index(dataframe):
    """
    Retorna:
    - DataFrame filtrado com colunas de índice de refração mescladas.
    """
    original_df = dataframe.copy()  # Armazena o DataFrame inicial para preservar os dados originais

    # Identifica colunas com valores fora do intervalo (1, 5), ignorando valores iguais a 0
    mask_out_of_range = (dataframe != 0) & ((dataframe < 1) | (dataframe > 5))  # Máscara para valores fora do intervalo
    columns_to_drop = mask_out_of_range.any(axis=0)  # Colunas que possuem ao menos um valor fora do intervalo

    # Remove as colunas identificadas
    filtered_df = dataframe.loc[:, ~columns_to_drop]  # Mantém apenas colunas válidas
    
    desired_compounds = data["desired_compounds"]
    columns_to_keep = [col for col in filtered_df.columns if col not in desired_compounds]
    filtered_df = filtered_df[columns_to_keep]
    def should_keep_column(col_name):
        if 'density' in col_name.lower():
            return False
        return bool(re.search(r'(N|RI)', col_name, re.IGNORECASE)) or bool(re.search(r'refrac', col_name, re.IGNORECASE))
    columns_to_keep = [col for col in filtered_df.columns if should_keep_column(col)]
    filtered_df = filtered_df[columns_to_keep]

    columns_to_remove = filtered_df.columns
    original_df = original_df.drop(columns=columns_to_remove)
    # Conta o número de valores não nulos em cada linha
    non_zero_counts = (filtered_df != 0).sum(axis=1)

    # Calcula a soma dos valores não nulos para cada linha
    summed_refractive = filtered_df.sum(axis=1, skipna=True)

    # preenche com -1 se mais de 1 valor não nulo for encontrado
    summed_refractive[non_zero_counts > 1] = -1
    
    rows_with_multiple_non0 = non_zero_counts > 1
    multiple_non_0 = filtered_df.where(rows_with_multiple_non0, other=0)
    # original_df = original_df.drop()
    dataframe_with_merged_ri = pd.concat([original_df, summed_refractive.rename("TERMINA AQUI"), multiple_non_0], axis=1)

    return dataframe_with_merged_ri




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
    final_filtered = merge_refractive_index(final_filtered)
    return final_filtered, excluded_by_removeemptycolumns, excluded_by_sumlines, excluded_by_filterbynotplus, excluded_by_removerowswithna

final_filtered, excluded_by_removeemptycolumns, excluded_by_sumlines, excluded_by_filterbynotplus, excluded_by_removerowswithna = all_filters(dataframe_t)

# Imprimindo o tamanho da tabela final  e das tabelas excluidas

filtered_path = Path("data/filtered")

final_filtered.to_csv                 (filtered_path / 'final_df.csv',                       index = False)
excluded_by_removeemptycolumns.to_csv (filtered_path / 'excluded_by_removeemptycolumns.csv', index = False)
excluded_by_sumlines.to_csv           (filtered_path / 'excluded_by_sumlines.csv',           index = False)
excluded_by_filterbynotplus.to_csv    (filtered_path / 'excluded_by_filterbynotplus.csv',    index = False)
excluded_by_removerowswithna.to_csv   (filtered_path / 'excluded_by_removerowswithna.csv',   index = False)

print(f"Tamanho do dataframe original: {dataframe_t.shape}")
print(f"Tamanho da tabela final: {final_filtered.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro que remove colunas vazias: {excluded_by_removeemptycolumns.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro da soma das linhas: {excluded_by_sumlines.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro de ter + no nome da col: {excluded_by_filterbynotplus.shape}")
print(f"Tamanho da tabela dos excluídos pelo filtro de remover linhas com NaN: {excluded_by_removerowswithna.shape}")
