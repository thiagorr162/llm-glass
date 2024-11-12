import json
import pathlib
import re
import unicodedata

import pandas as pd


def normalize_string(s):
    """Normaliza as strings removendo acentos e convertendo para minúsculas."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())


def check_if_desired(text):
    normalized_t = normalize_string(text)
    if any(desired in normalized_t for desired in desired_compounds):
        return True
    else:
        return False


input_path = pathlib.Path("data/patents")


properties_file = pathlib.Path("json/properties.json")

with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]


for table_file in input_path.rglob("*/processed/splitted/*.csv"):
    try:
        df = pd.read_csv(table_file, header=None)
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

    except pd.errors.ParserError:
        print(f"error parsing with pandas:{table_file}")
        # with open(table_file, "r") as f:
        #     txt_table = f.read()

    # all_tables = txt_table.split("\n\n")

    # correct_tables = []

    # for t in all_tables:
    #     if check_if_desired(t):
    #         correct_tables.append(t)

    # glass_examples = []

    # for i, t in enumerate(correct_tables):
    #     if t.lower().count("exemp") > 1:
    #         all_examples = t.lower().split("exemp")

    #         for ex in all_examples:
    #             if check_if_desired(ex):
    #                 glass_examples.append(ex)
    #     else:
    #         glass_examples = correct_tables.copy()

    # for i, t in enumerate(glass_examples):
    #     output_file = output_path / (f"{table_file.stem}-{i}.csv")

    #     with open(output_file, mode="w", encoding="utf-8") as file:
    #         file.write(t)