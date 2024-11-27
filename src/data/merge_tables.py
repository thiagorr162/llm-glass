import pathlib
import pandas as pd

# Caminhos de entrada e saída
input_path = pathlib.Path("data/patents")
output_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")  # Este arquivo não é utilizado aqui, mas mantido conforme o original.

def merge_csv_files(input_folder, output_file):
    """
    Mescla todos os arquivos CSV de um diretório em um único DataFrame e o salva no disco.

    Args:
        input_folder (pathlib.Path): Caminho para a pasta que contém os CSVs.
        output_file (pathlib.Path): Caminho para o arquivo de saída.
    """
    all_dfs = []
    for table_file in input_folder.rglob("*/processed/dataframe/*.csv"):
        try:
            df = pd.read_csv(table_file)
            all_dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler o arquivo {table_file}: {e}")

    if not all_dfs:
        print("Nenhum arquivo CSV encontrado para mesclar.")
        return

    try:
        merged_df = pd.concat(all_dfs, join="outer", ignore_index=True)
        merged_df.to_csv(output_file, index=False)
        print(f"DataFrame mesclado salvo em: {output_file}")
        print("Tamanho do DataFrame gerado:", merged_df.shape)
    except Exception as e:
        print(f"Erro ao mesclar ou salvar os arquivos CSV: {e}")

# Executa a função de mesclagem
merge_csv_files(input_path, output_path / "merged_df.csv")
print("Operação concluída com êxito.")