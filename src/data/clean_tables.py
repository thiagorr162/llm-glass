import csv
import json
from pathlib import Path

from bs4 import BeautifulSoup


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


# Definir o caminho para a pasta dos JSONs e de saída para as tabelas
json_folder = Path("data/patents")
output_folder = Path("data/tables")
output_folder.mkdir(parents=True, exist_ok=True)  # Criar a pasta de saída, se não existir

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

            # Encontrar as tabelas dentro de <patent-tables>
            tables = patent_table.find_all("table")

            # Processar cada tabela
            for i, table in enumerate(tables, start=1):
                table_data = html_table_to_list(table)

                # Gerar o nome do arquivo CSV baseado no nome do arquivo JSON
                output_file = output_folder / f"{json_file.stem}_table_{idx}_{i}.csv"

                # Salvar a tabela como CSV
                with output_file.open(mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerows(table_data)

                print(f"Tabela salva em {output_file}")
        else:
            print(f"Nenhuma tag <patent-tables> encontrada no arquivo {json_file.name}")
            breakpoint()
