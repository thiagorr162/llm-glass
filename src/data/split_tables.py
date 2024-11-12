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


input_path = pathlib.Path("data/patents")

properties_file = pathlib.Path("json/properties.json")

with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]


for table_file in input_path.rglob("*/good_tables/*.csv"):
    with open(table_file, "r", encoding="utf-8") as f:
        txt_table = f.read()

    txt_table = txt_table.replace('""', "")

    txt_table = txt_table.replace(",,", ",-,")

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

    output_path = table_file.parents[2] / "processed/splitted"
    output_path.mkdir(exist_ok=True, parents=True)

    for i, t in enumerate(glass_examples):
        output_file = output_path / (f"{table_file.stem}-{i}.csv")

        # Filtrando linhas com mais de uma vírgula antes de salvar
        filtered_lines = "\n".join(line for line in t.splitlines() if line.count(",") > 1)

        with open(output_file, mode="w", encoding="utf-8") as file:
            file.write(filtered_lines)
