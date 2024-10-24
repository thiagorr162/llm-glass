import json
import pathlib
import re
import unicodedata


def normalize_string(s):
    """Normaliza as strings removendo acentos e convertendo para minúsculas."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())


def check_if_desired(text):
    normalized_t = normalize_string(text)
    if any(desired in normalized_t for desired in desired_compounds):
        return True
    else:
        return False


input_path = pathlib.Path("data/tables/desired")
output_path = pathlib.Path("data/processed/has_compounds")
output_path.mkdir(parents=True, exist_ok=True)

properties_file = pathlib.Path("json/properties.json")

with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]


for table_file in input_path.rglob("*.csv"):
    with open(table_file, "r") as f:
        txt_table = f.read()

    txt_table = txt_table.replace('""', "")

    all_tables = txt_table.split("\n\n")

    correct_tables = []

    for t in all_tables:
        if check_if_desired(t):
            correct_tables.append(t)

    glass_examples = []

    for i, t in enumerate(correct_tables):
        if t.lower().count("exemp") > 1:
            all_examples = t.lower().split("exemp")

            for ex in all_examples:
                if check_if_desired(ex):
                    glass_examples.append(ex)
        else:
            glass_examples = correct_tables.copy()

    for i, t in enumerate(glass_examples):
        output_file = output_path / (f"{table_file.stem}_{i}.csv")

        with open(output_file, mode="w", encoding="utf-8") as file:
            file.write(t)
