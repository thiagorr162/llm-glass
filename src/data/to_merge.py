import pathlib
import shutil

# This code saves all csvs that have to be merged on a new folder "data/patents/to_merge"
input_path = pathlib.Path("data/patents")
output_path = pathlib.Path("data/patents/to_merge")

output_path.mkdir(parents=True, exist_ok=True)

def copiar_csvs(input_folder, output_folder):
    for table_file in input_folder.rglob("*/processed/dataframe/*.csv"):
        try:
            output_file = output_folder / table_file.name
            shutil.copy2(table_file, output_file)
            print(f"Copiado: {table_file} -> {output_file}")
        except Exception as e:
            print(f"Erro ao copiar {table_file}: {e}")

copiar_csvs(input_path, output_path)
print("Cópia concluída com sucesso.")
