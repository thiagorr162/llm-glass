import csv
import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup


def normalize_string(s):
    """Normaliza as strings removendo acentos e convertendo para minúsculas."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())


def html_table_to_list(table):
    """Converte uma tabela HTML para uma lista de listas (linhas e colunas)."""
    rows = table.find_all("tr")
    table_data = []

    for row in rows:
        columns = row.find_all("td")
        row_data = [col.get_text(strip=True) for col in columns]
        if row_data:  # Somente adicionar se houver dados
            table_data.append(row_data)

    return table_data


properties_file = Path("json/properties.json")

with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]


# Definir o caminho para a pasta dos JSONs e de saída para as tabelas
json_folder = Path("data/patents")

desired_output_folder = Path("data/tables/desired")
non_desired_output_folder = Path("data/tables/non_desired")
desired_output_folder.mkdir(parents=True, exist_ok=True)  # Criar a pasta de saída, se não existir
non_desired_output_folder.mkdir(parents=True, exist_ok=True)


# Iterar sobre todos os arquivos JSON na pasta
for json_file in json_folder.glob("*.json"):
    # Abrir e ler o arquivo JSON
    with json_file.open(encoding="utf-8") as f:
        data = json.load(f)

    # Verificar se existem tabelas no campo "html_tables"
    if not data.get("html_tables"):
        continue  # Pular este arquivo JSON se não houver tabelas

    # Processar cada bloco de tabelas no JSON
    for idx, patent_tables in enumerate(data["html_tables"], start=1):
        soup = BeautifulSoup(patent_tables, "html.parser")

        # Encontrar todas as tags <patent-tables>
        patent_table_elements = soup.find_all("patent-tables")

        # Verificar se há mais de uma tag <patent-tables>
        if len(patent_table_elements) > 1:
            print(f"Mais de uma tag <patent-tables> encontrada no arquivo {json_file.name}")
            breakpoint()  # Parar para depuração, se necessário

        # Processar a primeira (e possivelmente única) tag <patent-tables>
        if patent_table_elements:
            patent_table = patent_table_elements[0]

            table_data = html_table_to_list(patent_table)

            contains_desired = False
            for row in table_data:
                for cell in row:
                    normalized_cell = normalize_string(cell)
                    if any(desired in normalized_cell for desired in desired_compounds):
                        contains_desired = True
                        break
                if contains_desired:
                    break

            # Gerar o nome do arquivo CSV baseado no nome do arquivo JSON
            if contains_desired:
                output_file = desired_output_folder / f"{json_file.stem}-table_{idx}.csv"
            else:
                output_file = non_desired_output_folder / f"{json_file.stem}-table_{idx}.csv"

            # Salvar a tabela como CSV
            with output_file.open(mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=",")
                writer.writerows(table_data)

            print(f"Tabela salva em {output_file}")
        else:
            print(f"Nenhuma tag <patent-tables> encontrada no arquivo {json_file.name}")
            breakpoint()
