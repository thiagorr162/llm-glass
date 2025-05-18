from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Pasta onde estão os CSVs processados
input_folder = Path("data/patents/processing")

# Lista todos os arquivos CSV recursivamente
csv_files = list(input_folder.rglob("splited/*.csv"))

dfs = []

for file in tqdm(csv_files, desc="Lendo CSVs com cabeçalho"):
    try:
        df = pd.read_csv(file, header=0)  # Usa a primeira linha como header
        dfs.append(df)
    except Exception as e:
        print(f"Erro ao ler {file}: {e}")

# Faz o merge pelas colunas, alinhando pelo nome
merged_df = pd.concat(dfs, axis=0, join="outer", ignore_index=True)

# Caminho de saída
output_path = input_folder / "merged.csv"
merged_df.to_csv(output_path, index=False)

print(f"Merged CSV salvo em: {output_path}")
