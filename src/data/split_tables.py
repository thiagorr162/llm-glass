import json
import pathlib
import re
import unicodedata
import shutil

def normalize_string(s):
    """Normaliza as strings removendo acentos e convertendo para minúsculas."""
    return re.sub(
        r"\s+", "",
        unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower()
    )

def check_if_desired(text):
    """Verifica se o texto contém compostos desejados."""
    normalized_t = normalize_string(text)
    return any(desired in normalized_t for desired in desired_compounds)

def copy_to_not_splited(src_path, dest_folder):
    """Copia um arquivo para a pasta 'not_splited', tratando duplicatas."""
    destination = dest_folder / src_path.name
    if destination.exists():
        parent_folder = src_path.parent.parent.name
        destination = dest_folder / f"{src_path.stem}_{parent_folder}.csv"
    try:
        shutil.copy(src_path, destination)
        print(f"Arquivo copiado para: {destination}")
    except Exception as e:
        print(f"Erro ao copiar {src_path} para {dest_folder}: {e}")

def preprocess_table_text(text):
    """Aplica substituições no texto da tabela para normalização."""
    text = text.replace('""', "")
    text = text.replace(",,", ",-,")
    return text

def split_by_examples(table):
    """Divide uma tabela em exemplos com base na palavra 'exemp'."""
    if "exemp" in table.lower():
        return [ex for ex in table.lower().split("exemp") if check_if_desired(ex)]
    return [table]

def filter_desired_tables(tables):
    """Filtra tabelas que contêm compostos desejados."""
    return [table for table in tables if check_if_desired(table)]

def filter_lines_with_commas(lines):
    """Filtra linhas que contêm mais de uma vírgula."""
    return "\n".join(line for line in lines if line.count(",") > 1)

# Caminhos de entrada e propriedades
input_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")
not_splited_path = input_path / "not_splited"
not_splited_path.mkdir(parents=True, exist_ok=True)

# Compostos desejados
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]

# Processamento de arquivos
for table_file in input_path.rglob("*/good_tables/*.csv"):
    try:
        with table_file.open("r", encoding='utf-8') as f:
            txt_table = preprocess_table_text(f.read())

        all_tables = txt_table.split("\n\n")
        correct_tables = filter_desired_tables(all_tables)

        glass_examples = []
        for t in correct_tables:
            glass_examples.extend(split_by_examples(t))

        output_path = table_file.parents[2] / "processed/splitted"
        output_path.mkdir(parents=True, exist_ok=True)

        if glass_examples:
            for i, t in enumerate(glass_examples):
                output_file = output_path / f"{table_file.stem}-{i}.csv"
                filtered_lines = filter_lines_with_commas(t.splitlines())
                with output_file.open(mode="w", encoding="utf-8") as file:
                    file.write(filtered_lines)
            print(f"Arquivo processado e salvo em: {output_path}")
        else:
            copy_to_not_splited(table_file, not_splited_path)

    except Exception as e:
        print(f"Erro ao processar {table_file}: {e}")
        copy_to_not_splited(table_file, not_splited_path)

print("Operação concluída com êxito.")
