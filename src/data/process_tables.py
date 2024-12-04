import json
import pathlib
import re
import unicodedata
import shutil
import pandas as pd
import csv

# Função para normalizar strings: remove espaços, acentos e converte para letras minúsculas
def normalize_string(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s)
                  .encode("ASCII", "ignore").decode("utf-8").lower())

# Função para verificar se um valor é numérico
def is_numeric(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

# Função para copiar arquivos não processados para uma pasta de destino
def copy_to_not_processed(src_path, dest_folder):
    destination = dest_folder / src_path.name
    counter = 1

    # Adiciona um sufixo numérico se o arquivo já existir para evitar sobrescrita
    while destination.exists():
        destination = dest_folder / f"{src_path.stem}_{counter}{src_path.suffix}"
        counter += 1

    try:
        shutil.copy(src_path, destination)
        print(f"Arquivo copiado para: {destination}")
    except Exception as e:
        print(f"Falha ao copiar {src_path} para 'not_processed': {e}")

# Configuração dos caminhos
input_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")
not_processed_path = input_path / "not_processed"
not_processed_path.mkdir(parents=True, exist_ok=True)

# Carrega os compostos desejados do arquivo JSON e normaliza os nomes
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) 
                         for compound in properties_data.get("desired_compounds", [])]

# Itera por todos os arquivos CSV na estrutura especificada
for table_file in input_path.rglob("/processed/splitted/.csv"):
    try:
        # Lê o arquivo CSV em linhas
        with open(table_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Determina o número máximo de colunas
        max_columns = max(len(row) for row in rows)

        # Lista para armazenar informações sobre cada linha
        rows_info = []
        max_first_numeric_idx = 0

        # Analisa cada linha para identificar a posição do primeiro valor numérico
        for row in rows:
            first_numeric_idx = None
            for idx, val in enumerate(row):
                val_strip = val.strip()
                if val_strip in ['', '-', ' ']:
                    continue  # Valor NaN
                elif is_numeric(val_strip):
                    first_numeric_idx = idx
                    break  # Primeiro valor numérico encontrado
            if first_numeric_idx is None:
                first_numeric_idx = len(row)  # Nenhum valor numérico encontrado
            if first_numeric_idx > max_first_numeric_idx:
                max_first_numeric_idx = first_numeric_idx
            rows_info.append({
                'row': row,
                'first_numeric_idx': first_numeric_idx
            })

        # Ajusta cada linha com base no índice máximo do primeiro valor numérico
        adjusted_rows = []
        for info in rows_info:
            row = info['row']
            first_numeric_idx = info['first_numeric_idx']
            shift = max_first_numeric_idx - first_numeric_idx
            if shift > 0:
                # Insere NaNs para alinhar os valores numéricos
                row = row + ['-'] * shift
            # Preenche com NaNs à direita para garantir o mesmo número de colunas
            row += ['-'] * (max_columns - len(row))
            adjusted_rows.append(row)

        # Reescreve o arquivo CSV com as linhas ajustadas
        with open(table_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(adjusted_rows)

        # Carrega o arquivo CSV em um DataFrame do pandas
        df = pd.read_csv(table_file, encoding='utf-8', delimiter=',', header=None)
        df = df.dropna(axis=1, how="all").T  # Remove colunas completamente vazias e transpõe

        # Encontra o índice do cabeçalho contendo os compostos desejados
        header_idx = next(
            (idx for idx, row in enumerate(df.values)
             if any(normalize_string(str(h)) in desired_compounds for h in row)),
            None
        )

        if header_idx is not None:
            # Cria um novo DataFrame usando o cabeçalho encontrado
            new_header = df.iloc[header_idx]
            new_df = df[header_idx + 1:].copy()
            new_df.columns = new_header

            # Adiciona uma coluna com o caminho do arquivo atual
            new_df['IDS'] = str(table_file)

            # Define o caminho de saída para salvar o DataFrame processado
            output_path = table_file.parents[1] / "dataframe"
            output_path.mkdir(parents=True, exist_ok=True)
            new_df.to_csv(output_path / (table_file.stem + ".csv"), index=False)
        else:
            # Move o arquivo para 'not_processed' se nenhum composto desejado for encontrado
            print(f"AVISO: Nenhum composto desejado encontrado no cabeçalho: {table_file}")
            copy_to_not_processed(table_file, not_processed_path)

    except Exception as e:
        # Tratamento geral de erros
        print(f"ERRO: {e} em {table_file}")
        copy_to_not_processed(table_file, not_processed_path)

# Mensagem final indicando que o processamento foi concluído
print("Operação concluída com êxito.")
