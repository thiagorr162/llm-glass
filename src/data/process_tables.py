import json
import pathlib
import re
import unicodedata
import shutil
import pandas as pd
import csv

# Função para normalizar strings: remove espaços, acentos e converte para letras minúsculas
def normalize_string(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())

# Função para copiar arquivos não processados para uma pasta de destino
def copy_to_not_processed(src_path, dest_folder):
    # Define o caminho de destino com base no nome do arquivo de origem
    destination = dest_folder / src_path.name
    # Evita sobrescrita adicionando o nome do subdiretório pai ao nome do arquivo, se necessário
    if destination.exists():
        parent_folder = src_path.parent.parent.name
        destination = dest_folder / f"{src_path.stem}_{parent_folder}.csv"
    try:
        # Copia o arquivo para o destino
        shutil.copy(src_path, destination)  
    except Exception as e:
        # Exibe mensagem de erro em caso de falha na cópia
        print(f"      Falha ao copiar {src_path} para 'not_processed': {e}")

# Define o caminho de entrada para os arquivos de patentes
input_path = pathlib.Path("data/patents")
# Define o caminho para o arquivo JSON com propriedades desejadas
properties_file = pathlib.Path("json/properties.json")
# Define o caminho para a pasta de arquivos não processados
not_processed_path = input_path / "not_processed"
# Cria a pasta 'not_processed' se ela não existir
not_processed_path.mkdir(parents=True, exist_ok=True)

# Carrega os compostos desejados do arquivo JSON e normaliza os nomes
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]

# Itera por todos os arquivos CSV na estrutura especificada
for table_file in input_path.rglob("*/processed/splitted/*.csv"):
    try:
        # Lê o arquivo CSV em linhas para verificar o número de colunas
        with open(table_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
        
        # Garante que todas as linhas tenham o mesmo número de colunas
        max_columns = max(len(row) for row in rows)
        equalized_rows = [row + [''] * (max_columns - len(row)) for row in rows]
        
        # Reescreve o arquivo com colunas ajustadas
        with open(table_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(equalized_rows)
        
        # Carrega o arquivo CSV em um DataFrame do pandas, transpondo-o para facilitar o processamento
        df = pd.read_csv(table_file, encoding='utf-8', delimiter=',', header=None)
        df = df.dropna(axis=1, how="all").T  # Remove colunas completamente vazias e transpõe o DataFrame

        # Encontra o índice do cabeçalho contendo os compostos desejados
        header_idx = next(
            (idx for idx, row in enumerate(df.values) 
             if any(normalize_string(str(h)) in desired_compounds for h in row)), 
            None
        )

        if header_idx is not None:
            # Se o cabeçalho for encontrado, cria um novo DataFrame a partir dele
            new_header = df.iloc[header_idx]
            new_df = df[header_idx + 1:].copy()  # Exclui o cabeçalho e mantém os dados
            new_df.columns = new_header  # Define as colunas do novo DataFrame com o cabeçalho encontrado
            
            # Adiciona a coluna com o nome do arquivo atual
            new_df['IDS'] = table_file  # Adiciona o caminho do arquivo em cada linha
            
            # Define o caminho de saída para salvar o DataFrame processado
            output_path = table_file.parents[1] / "dataframe"
            output_path.mkdir(parents=True, exist_ok=True)  # Cria a pasta de saída se não existir
            new_df.to_csv(output_path / (table_file.stem + ".csv"), index=False)  # Salva o DataFrame
            print(f"OK   Arquivo processado e salvo em: {output_path}")
        else:
            # Se nenhum cabeçalho correspondente for encontrado, move o arquivo para 'not_processed'
            print(f"AVISO: Nenhum composto desejado encontrado no cabeçalho: {table_file}")
            copy_to_not_processed(table_file, not_processed_path)

    except Exception as e:
        # Tratamento geral de erros
        print(f"ERRO: {e} em {table_file}")
        copy_to_not_processed(table_file, not_processed_path)

# Mensagem final indicando que o processamento foi concluído
print("Operação concluída com êxito.")
