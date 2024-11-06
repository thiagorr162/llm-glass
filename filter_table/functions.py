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
    excluded_columns = dataframe.columns.difference(filtered_columns)
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
    dataframe = insert_zeros(dataframe)
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
    filtered_dataframe, _ = Filter_By_Compounds(dataframe)
    columns = filtered_dataframe.columns
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
    excluded_columns = dataframe.columns.difference(filtered_columns)
    return dataframe[filtered_columns], dataframe[excluded_columns]

def dataframe_sum_and_properties(dataframe):
    """
    Returns:
    - Filtered DataFrame with rows summing to 100 and columns of specified properties.
    - Excluded DataFrame with rows not meeting the criteria.
    """
    filtered_dataframe, _ = Filter_By_Compounds(dataframe)
    rows_with_sum_100, _ = sum_lines(dataframe)
    properties_columns, _ = filter_by_properties(dataframe)
    filtered_data = filtered_dataframe.loc[rows_with_sum_100.index]
    properties_non_null = dataframe[properties_columns].sum(axis=1) != 0
    final_filtered = pd.concat([filtered_data, dataframe[properties_columns].loc[properties_non_null]], axis=1)
    excluded_rows = dataframe.drop(rows_with_sum_100.index)
    return final_filtered, excluded_rows

def all_filters(dataframe):
    """
    Returns
    - Final Filtered DataFrame
    - Final Excluded DataFrame
    """

    # Normaliza o dataframe para podermos usar os demais filtros
    dataframe = insert_zeros(dataframe)
    dataframe, null_columns = remove_empty_columns(dataframe)
    dataframe, has_plus = Filter_by_not_plus(dataframe)

    # Aplica o filtro de compostos
    compounds, not_compounds = Filter_By_Compounds(dataframe)
    # O filtro das linhas somarem 100 deve incidir somente no dataframe que contém apenas compostos
    compounds, sum_not_100 = sum_lines(compounds)

    # Atualiza o dataframe para conter apenas colunas que sobraram
    dataframe = compounds

    # Filtragem por propriedades no dataframe já filtrado
    properties, not_properties = filter_by_properties(dataframe)

    # Colunas excluídas que não são compostos nem propriedades
    excluded = pd.concat([not_compounds, not_properties]).drop_duplicates()
    
    # Combinações finais do dataframe filtrado
    final_filtered_dataframe = pd.concat([compounds, properties], axis=1)
    
    return final_filtered_dataframe, null_columns, has_plus, sum_not_100, excluded

# teste do filtro final thomaz
final_df, null_columns, has_plus, sum_not_100, excluded = all_filters(dataframe3)

# salvando os arquivos novos
new_path = Path("filter_table/filtered")

final_df.to_csv(new_path / 'final_df.csv', index=False)
null_columns.to_csv(new_path / 'null_columns.csv', index=False)
has_plus.to_csv(new_path / 'has_plus.csv', index=False)
sum_not_100.to_csv(new_path / 'sum_not_100.csv', index=False)
excluded.to_csv(new_path / 'excluded.csv', index=False)

print("Dataframe final:\n", final_df)
print("Dataframe das colunas nulas excluídas pelo filtro:\n", null_columns)
print("Dataframe das colunas excluídas por ter +:\n", has_plus)
print("Dataframe das linhas de compostos excluídas por não somarem entre 98 e 102:\n", sum_not_100)
print("Dataframe das colunas excluídas que não são nem compostos nem propriedades:\n", excluded)