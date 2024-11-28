import json
import pathlib
import re
import unicodedata
import shutil

# Função para normalizar strings: remove espaços, acentos e converte para minúsculas
def normalize_string(s):
    """Normaliza strings removendo acentos, espaços e convertendo para minúsculas."""
    return re.sub(
        r"\s+", "",
        unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower()
    )

# Função para verificar se um texto contém compostos desejados
def check_if_desired(text):
    """Verifica se o texto contém algum composto desejado."""
    normalized_text = normalize_string(text)
    return any(compound in normalized_text for compound in desired_compounds)

# Caminhos principais
input_path = pathlib.Path("data/patents")  # Caminho de entrada
properties_file = pathlib.Path("json/properties.json")  # Arquivo JSON com propriedades
not_splited_path = input_path / "not_splited"  # Pasta para arquivos não divididos
not_splited_path.mkdir(parents=True, exist_ok=True)  # Criar pasta, se não existir

# Carregar compostos desejados
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(c) for c in properties_data.get("desired_compounds", [])]

# Processar cada arquivo CSV na pasta 'good_tables'
for table_file in input_path.rglob("*/good_tables/*.csv"):
    try:
        # Ler conteúdo do arquivo
        with table_file.open("r", encoding="utf-8") as f:
            txt_table = f.read()

        # Ajustes no texto do arquivo
        txt_table = txt_table.replace('""', "").replace(",,", ",-,")
        all_tables = txt_table.split("\n\n")  # Divisão por quebra de linha dupla

        # Filtrar tabelas com compostos desejados
        correct_tables = [t for t in all_tables if check_if_desired(t)]
        glass_examples = []

        # Separar exemplos nas tabelas filtradas
        for t in correct_tables:
            examples = t.lower().split("exemp") if t.lower().count("exemp") > 1 else [t]
            glass_examples.extend(ex for ex in examples if check_if_desired(ex))

        # Criar caminho de saída
        output_path = table_file.parents[2] / "processed/splitted"
        output_path.mkdir(parents=True, exist_ok=True)

        if glass_examples:
            # Salvar tabelas filtradas
            for i, example in enumerate(glass_examples):
                output_file = output_path / f"{table_file.stem}-{i}.csv" if len(glass_examples) > 1 else output_path / f"{table_file.stem}.csv"
                filtered_lines = "\n".join(line for line in example.splitlines() if line.count(",") > 1)

                with output_file.open("w", encoding="utf-8") as file:
                    file.write(filtered_lines)
            print(f"Arquivo salvo: {output_file}")

        else:
            # Copiar arquivo problemático para 'not_splited'
            destination = not_splited_path / table_file.name
            if destination.exists():
                parent_folder = table_file.parent.parent.name
                destination = not_splited_path / f"{table_file.stem}_{parent_folder}.csv"
            shutil.copy(table_file, destination)
            print(f"Arquivo sem tabelas relevantes copiado para: {destination}")

    except Exception as e:
        # Em caso de erro, copiar para 'not_splited'
        destination = not_splited_path / table_file.name
        if destination.exists():
            parent_folder = table_file.parent.parent.name
            destination = not_splited_path / f"{table_file.stem}_{parent_folder}.csv"
        shutil.copy(table_file, destination)
        print(f"Erro ao processar {table_file}: {e}. Arquivo copiado para: {destination}")

# Indicar a conclusão da operação
print("Operação concluída com êxito.")
    