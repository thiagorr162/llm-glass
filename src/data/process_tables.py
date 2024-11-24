import json
import pathlib
import re
import unicodedata
import shutil  # Import necessário para copiar arquivos

import pandas as pd


def normalize_string(s):
    """Normaliza as strings removendo acentos e convertendo para minúsculas."""
    return re.sub(
        r"\s+", "",
        unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower()
    )


def check_if_desired(text):
    normalized_t = normalize_string(text)
    return any(desired in normalized_t for desired in desired_compounds)


# Defina os caminhos de entrada e propriedades
input_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")

# Defina o caminho para a pasta 'not_processed'
not_processed_path = input_path / "not_processed"
not_processed_path.mkdir(parents=True, exist_ok=True)  # Cria a pasta se não existir

# Carregue os compostos desejados
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]

# Iterar sobre todos os arquivos .csv dentro de 'processed/splitted'
for table_file in input_path.rglob("*/processed/splitted/*.csv"):
    try:
        df = pd.read_csv(table_file, encoding='utf-8', delimiter=',', header=None)
        df = df.dropna(axis=1, how="all")

        df = df.T

        n_rows = df.shape[0]

        header_idx = 0
        new_header = df.iloc[header_idx]

        n_compounds = len([str(h).lower() for h in new_header if str(h).lower() in desired_compounds])

        while n_compounds == 0 and header_idx < n_rows:
            new_header = df.iloc[header_idx]
            n_compounds = len([str(h).lower() for h in new_header if str(h).lower() in desired_compounds])
            header_idx += 1

        header_idx = header_idx + 1
        new_df = df[header_idx:].copy()
        new_df.columns = new_header

        output_path = table_file.parents[1] / "dataframe"
        output_path.mkdir(parents=True, exist_ok=True)

        new_df.to_csv(output_path / (table_file.stem + ".csv"), index=False)
        print(f"OK   Arquivo processado e salvo em: {output_path}")

    except pd.errors.ParserError:
        print(f"PARSE Erro ao parsear com pandas: {table_file}")

        # Copiar o arquivo para 'not_processed'
        destination = not_processed_path / table_file.name

        # Lidar com possíveis duplicatas adicionando o nome da pasta pai
        if destination.exists():
            parent_folder = table_file.parent.parent.name  # Ajuste conforme a estrutura de pastas
            destination = not_processed_path / f"{table_file.stem}_{parent_folder}.csv"
        try:
            shutil.copy(table_file, destination)
            print(f"      Arquivo não processado copiado para: {destination}")
        except Exception as copy_error:
            print(f"      Falha ao copiar {table_file} para 'not_processed': {copy_error}")

    except pd.errors.EmptyDataError:
        print(f"VAZIA Erro de tabela vazia {table_file}")

        # Copiar o arquivo para 'not_processed'
        destination = not_processed_path / table_file.name
    
        # Lidar com possíveis duplicatas adicionando o nome da pasta pai
        if destination.exists():
            parent_folder = table_file.parent.parent.name  # Ajuste conforme a estrutura de pastas
            destination = not_processed_path / f"{table_file.stem}_{parent_folder}.csv"

        try:
            shutil.copy(table_file, destination)
            print(f"      Arquivo não processado copiado para: {destination}")
        except Exception as copy_error:
            print(f"      Falha ao copiar {table_file} para 'not_processed': {copy_error}")

print("Operação concluída com êxito.")