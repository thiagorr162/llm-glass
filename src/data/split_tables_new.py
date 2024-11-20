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
    normalized_t = normalize_string(text)
    return any(desired in normalized_t for desired in desired_compounds)

# Defina os caminhos de entrada e propriedades
input_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")

# Defina o caminho para a pasta 'not_splited'
not_splited_path = input_path / "not_splited"
not_splited_path.mkdir(parents=True, exist_ok=True)  # Cria a pasta se não existir

# Carregue os compostos desejados
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]

# Iterar sobre todos os arquivos .csv dentro de 'good_tables'
for table_file in input_path.rglob("*/good_tables/*.csv"):
    try:
        with table_file.open("r", encoding='utf-8') as f:
            txt_table = f.read()

        # Realizar substituições no texto
        txt_table = txt_table.replace('""', "")
        txt_table = txt_table.replace(",,", ",-,")

        # Dividir o texto em possíveis tabelas
        all_tables = txt_table.split("\n\n")

        # Filtrar tabelas que contêm compostos desejados
        correct_tables = [t for t in all_tables if check_if_desired(t)]

        glass_examples = []

        # Dividir tabelas com base na ocorrência de "exemp"
        for t in correct_tables:
            if t.lower().count("exemp") > 1:
                all_examples = t.lower().split("exemp")
                for ex in all_examples:
                    if check_if_desired(ex):
                        glass_examples.append(ex)
            else:
                glass_examples = correct_tables.copy()
                break  # Não é necessário continuar se não há múltiplos "exemp"

        # Definir o caminho de saída para tabelas divididas
        output_path = table_file.parents[2] / "processed/splitted"
        output_path.mkdir(parents=True, exist_ok=True)

        if len(glass_examples) > 1:
            # O arquivo foi dividido em múltiplas partes
            for i, t in enumerate(glass_examples):
                output_file = output_path / f"{table_file.stem}-{i}.csv"

                # Filtrar linhas com mais de uma vírgula
                filtered_lines = "\n".join(
                    line for line in t.splitlines() if line.count(",") > 1
                )

                with output_file.open(mode="w", encoding="utf-8") as file:
                    file.write(filtered_lines)
            print(f"Arquivo dividido e salvo em: {output_path}")
        elif len(glass_examples) == 1:
            # O arquivo não foi dividido, mas atende aos critérios; salvar em 'splitted'
            output_file = output_path / f"{table_file.stem}.csv"

            # Filtrar linhas com mais de uma vírgula
            filtered_lines = "\n".join(
                line for line in glass_examples[0].splitlines() if line.count(",") > 1
            )

            with output_file.open(mode="w", encoding="utf-8") as file:
                file.write(filtered_lines)
            print(f"Arquivo salvo em 'splitted' sem divisão: {output_file}")
        else:
            # Nenhuma tabela correta encontrada; copiar para 'not_splited'
            destination = not_splited_path / table_file.name

            # Lidar com possíveis duplicatas adicionando o nome da pasta pai
            if destination.exists():
                parent_folder = table_file.parent.parent.name  # Ajuste conforme a estrutura de pastas
                destination = not_splited_path / f"{table_file.stem}_{parent_folder}.csv"

            shutil.copy(table_file, destination)
            print(f"Arquivo não processado copiado para: {destination}")

    except Exception as e:
        # Em caso de erro, copiar para 'not_splited'
        destination = not_splited_path / table_file.name

        # Lidar com possíveis duplicatas adicionando o nome da pasta pai
        if destination.exists():
            parent_folder = table_file.parent.parent.name  # Ajuste conforme a estrutura de pastas
            destination = not_splited_path / f"{table_file.stem}_{parent_folder}.csv"

        shutil.copy(table_file, destination)
        print(f"Erro ao processar {table_file}: {e}. Arquivo copiado para: {destination}")
