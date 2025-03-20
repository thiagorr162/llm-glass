import pathlib
import pandas as pd

input_path = pathlib.Path("data/patents")
output_path = pathlib.Path("data/patents/to_merge")

output_path.mkdir(parents=True, exist_ok=True)

def saving_csvs(input_folder, output_folder):
    for table_file in input_folder.rglob("*/processed/dataframe/*.csv"):
        try:
            df = pd.read_csv(table_file)

            output_file = output_folder / table_file.name

            df.to_csv(output_file, index=False)
            print(f"Salvo: {output_file}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo {table_file}, {e}")


saving_csvs(input_path, output_path)
print("Operação concluída com sucesso.")
