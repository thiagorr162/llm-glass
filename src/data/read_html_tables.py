import csv
import json
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup


def normalize_string(s):
    """
    Normaliza uma string removendo acentos, espaços extras e convertendo para minúsculas.
    """
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())


def html_table_to_list(table):
    """
    Converte uma tabela HTML para uma lista de listas (linhas e colunas).
    """
    return [
        [col.get_text(strip=True) for col in row.find_all("td")]
        for row in table.find_all("tr")
        if row.find_all("td")  # Somente adicionar linhas com colunas válidas
    ]


# Carregar os compostos desejados do arquivo JSON
properties_file = Path("json/properties.json")
try:
    with properties_file.open(encoding="utf-8") as f:
        properties_data = json.load(f)
        desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Erro ao carregar o arquivo properties.json: {e}")
    desired_compounds = []

# Caminho da pasta dos JSONs
json_folder = Path("data/patents")

# Iterar sobre todos os arquivos JSON
for json_file in json_folder.rglob("*.json"):
    try:
        with json_file.open(encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao ler o arquivo {json_file.name}: {e}")
        continue

    # Verificar se existem tabelas no campo "html_tables"
    if not data.get("html_tables"):
        continue

    # Processar cada bloco de tabelas no JSON
    for idx, patent_tables in enumerate(data["html_tables"], start=1):
        soup = BeautifulSoup(patent_tables, "html.parser")
        patent_table_elements = soup.find_all("patent-tables")

        if len(patent_table_elements) > 1:
            print(f"Mais de uma tag <patent-tables> encontrada no arquivo {json_file.name}")

        # Processar a primeira (e possivelmente única) tag <patent-tables>
        if not patent_table_elements:
            print(f"Nenhuma tag <patent-tables> encontrada no arquivo {json_file.name}")
            continue

        patent_table = patent_table_elements[0]
        table_data = html_table_to_list(patent_table)

        # Verificar se a tabela contém compostos desejados
        contains_desired = any(
            any(desired in normalize_string(cell) for desired in desired_compounds)
            for row in table_data
            for cell in row
        )

        # Criar pastas de saída
        output_folder = json_file.parent / "tables" / ("good_tables" if contains_desired else "bad_tables")
        output_folder.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo CSV
        output_file = output_folder / f"{json_file.stem}-table_{idx}.csv"

        # Salvar a tabela como CSV
        try:
            with output_file.open(mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=",")
                writer.writerows(table_data)
            print(f"Tabela salva em {output_file}")
        except IOError as e:
            print(f"Erro ao salvar o arquivo {output_file.name}: {e}")

print("Operação concluída com êxito.")
