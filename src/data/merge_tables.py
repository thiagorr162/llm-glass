import pathlib

import pandas as pd

input_path = pathlib.Path("data/patents")

output_path = pathlib.Path("data/patents")

properties_file = pathlib.Path("json/properties.json")


all_dfs = []

for table_file in input_path.rglob("*/processed/dataframe/*.csv"):
    df = pd.read_csv(table_file)

    all_dfs.append(df)


merged_df = pd.concat(all_dfs, join="outer", ignore_index=True)

merged_df.to_csv(output_path / "merged_df.csv")

print("Tamanho do dataframe gerado:",merged_df.shape)

print("Operação concluída com êxito.")