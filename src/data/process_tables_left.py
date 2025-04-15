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
for table_file in input_path.rglob("processed/splitted/*.csv"):
    try:
        # Lê o arquivo CSV em linhas
        with open(table_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Primeiro, processa cada linha para identificar:
        # - O índice do primeiro valor numérico
        # - Quantos elementos faltantes (NaN representado por '-' ou strings vazias/espacos) existem antes dele ("shift left").
        rows_info = []
        max_left_gap = 0  # Armazena o maior número de NaNs anteriores ao primeiro numérico encontrado

        for row in rows:
            shift_left_count = 0
            first_numeric_idx = None
            # Itera sobre a linha para encontrar o primeiro valor numérico
            # e contar os NaN (células faltantes) antes dele.
            for idx, cell in enumerate(row):
                cell_strip = cell.strip()
                if cell_strip in ['', '-', ' ']:
                    shift_left_count += 1
                elif is_numeric(cell_strip):
                    first_numeric_idx = idx
                    break  # Para ao encontrar o primeiro valor numérico
                else:
                    # Caso o valor seja um rótulo (ex.: letras como "A", "B", "C") ou outro dado não numérico
                    # estes não são considerados gaps faltantes.
                    continue
            # Se nenhum valor numérico for encontrado, define o índice como o tamanho atual da linha.
            if first_numeric_idx is None:
                first_numeric_idx = len(row)
            if shift_left_count > max_left_gap:
                max_left_gap = shift_left_count
            rows_info.append({
                'row': row,
                'first_numeric_idx': first_numeric_idx,
                'shift_left_count': shift_left_count
            })

        # Ajusta cada linha aplicando o "shift left":
        # Se a quantidade de NaN antes do primeiro número (shift_left_count) for menor que max_left_gap,
        # insere-se NaN (representados por '-') antes do primeiro valor numérico.
        adjusted_rows = []
        for info in rows_info:
            row = info['row']
            f_idx = info['first_numeric_idx']
            left_count = info['shift_left_count']
            if left_count < max_left_gap:
                diff = max_left_gap - left_count
                row = row[:f_idx] + ['-'] * diff + row[f_idx:]
            adjusted_rows.append(row)

        # Após o ajuste à esquerda, verifica a quantidade total de elementos em cada linha.
        # Se alguma linha possuir menos elementos que as demais, insere-se NaN ao final para completá-la.
        max_total_columns = max(len(r) for r in adjusted_rows)
        final_rows = []
        for r in adjusted_rows:
            if len(r) < max_total_columns:
                r = r + ['-'] * (max_total_columns - len(r))
            final_rows.append(r)

        # Reescreve o arquivo CSV com as linhas ajustadas
        with open(table_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(final_rows)

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
            print(f"Tabela processada: {table_file} salva em: {output_path / (table_file.stem + '.csv')}")
        else:
            # Move o arquivo para 'not_processed' se nenhum composto desejado for encontrado
            print(f"AVISO: Nenhum composto desejado encontrado no cabeçalho: {table_file}")
            copy_to_not_processed(table_file, not_processed_path)

    except Exception as e:
        # Tratamento geral de erros
        print(f"ERRO: {e} em {table_file}")
        copy_to_not_processed(table_file, not_processed_path)

# Mensagem final indicando que o processamento foi concluído
print("Operação concluída com êxito.")
