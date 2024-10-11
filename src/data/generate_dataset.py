import json
from pathlib import Path

import pandas as pd

# Caminhos das pastas
csv_folder = Path("data/processed")
json_file = Path("json/properties.json")

# Carregar o JSON contendo os compostos desejados
with open(json_file, "r") as file:
    properties = json.load(file)

desired_compounds = set(properties["desired_compounds"])  # Usar set para acelerar busca

# Inicializar uma lista para armazenar os DataFrames que serão concatenados
dfs = []

# Processar todos os arquivos CSV na pasta
for csv_file in csv_folder.rglob("*.csv"):
    try:
        df = pd.read_csv(csv_file, header=None)
    except pd.errors.ParserError:
        print("Erro ao processar: ", csv_file)
        continue

    # Eliminar colunas que estão completamente vazias
    df.dropna(axis=1, how="all", inplace=True)

    # Obter a primeira coluna e verificar se há ao menos 2 compostos desejados
    first_column = df.iloc[:, 0].astype(str)
    matches = [compound for compound in desired_compounds if compound in first_column.to_string()]

    if len(matches) < 2:
        continue

    # Transpor o DataFrame
    df = df.T

    # Verificar e remover colunas duplicadas após a transposição
    if not df.iloc[0].is_unique:
        df = df.loc[:, ~df.iloc[0].duplicated()]

    # Renomear as colunas após a transposição, convertendo para minúsculas
    df.columns = df.iloc[0].str.lower()

    # Verificar e remover colunas duplicadas após a renomeação
    if not df.columns.is_unique:
        df = df.loc[:, ~df.columns.duplicated()]

    # Remover a primeira linha, que agora é o cabeçalho
    df = df[1:]

    # Adicionar uma coluna com o ID (extraído do diretório pai) e o nome da tabela (nome do arquivo CSV)
    csv_id = csv_file.parent.stem  # Diretório pai (ID)
    table_name = csv_file.stem  # Nome do arquivo CSV sem extensão

    df["csv_id"] = csv_id
    df["table_name"] = table_name

    dfs.append(df)

# Concatenar todos os DataFrames, unindo colunas compartilhadas
if dfs:
    final_df = pd.concat(dfs, join="outer", ignore_index=True)

    # Verificar e remover colunas duplicadas após a concatenação
    if not final_df.columns.is_unique:
        final_df = final_df.loc[:, ~final_df.columns.duplicated()]

    final_df.reset_index(drop=True, inplace=True)
    final_df.to_csv("data/processed/final_filtered_concatenated.csv", index=False)

    print("Concatenação completa. O arquivo final foi salvo em 'data/processed/final_filtered_concatenated.csv'.")
else:
    print("Nenhuma tabela correspondente foi encontrada.")
