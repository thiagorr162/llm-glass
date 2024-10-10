import argparse
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def extract_patent_id_from_url(url):
    """Extrai o ID da patente a partir da URL."""
    return url.split("/")[-1].split(".")[0]


def format_table_as_text(table):
    """Formata uma tabela HTML como texto separado por vírgula."""
    rows = table.find_all("tr")
    return "\n".join(",".join(col.get_text(strip=True) for col in row.find_all(["th", "td"])) for row in rows)


def contains_desired_compounds(table_text, desired_compounds):
    """Verifica se a tabela contém algum dos compostos desejados."""
    return any(compound in table_text for compound in desired_compounds)


def save_table_text(table_text, output_dir, table_idx):
    """Salva o texto formatado da tabela no arquivo .txt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    table_file_path = output_dir / f"table_{table_idx}.txt"
    with open(table_file_path, "w") as table_file:
        table_file.write(table_text)
    print(f"Tabela {table_idx} salva em '{table_file_path}'.")


def save_raw_tables_from_html(url, desired_compounds):
    """Acessa uma página de patente, processa tabelas e salva as que contêm compostos desejados."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        tables = soup.find_all("patent-tables")

        if not tables:
            print("Elemento '<patent-tables>' não encontrado na página.")
            return 0

        patent_id = extract_patent_id_from_url(url)
        output_dir = Path(f"data/patents/{patent_id}")
        saved_tables = 0

        for idx, table in enumerate(tables, start=1):
            table_text = format_table_as_text(table)
            if contains_desired_compounds(table_text, desired_compounds):
                save_table_text(table_text, output_dir, idx)
                saved_tables += 1

        if saved_tables == 0:
            print("Nenhuma tabela contém compostos desejados. Nenhum arquivo foi salvo.")

        return saved_tables

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return 0


def get_patent_links(search_url):
    """Obtém links de patentes de uma página de busca que contenham a palavra 'glass'."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    return [
        f"https://www.freepatentsonline.com{link['href']}"
        for link in soup.find_all("a", href=True)
        if "glass" in link.get_text().lower()
    ]


if __name__ == "__main__":
    """Processa páginas de patentes e salva as tabelas de interesse."""
    # Configuração do argparse
    parser = argparse.ArgumentParser(description="Busca e extrai tabelas de patentes.")
    parser.add_argument(
        "--page_max",
        "-p",
        type=int,
        default=1,
        help="Número máximo de páginas a serem buscadas",
    )
    parser.add_argument(
        "--keyword",
        "-k",
        type=str,
        default="glass composition",
        help="Palavra-chave para busca de patentes",
    )
    args = parser.parse_args()

    keyword = args.keyword.replace(" ", "+")

    with open("json/properties.json", "r") as json_file:
        desired_compounds = json.load(json_file)["desired_compounds"]

    for page in range(1, args.page_max + 1):
        search_url = (
            f"https://www.freepatentsonline.com/result.html?"
            f"p={page}&sort=relevance&srch=top&query_txt={keyword}&patents_us=on"
        )
        patent_links = get_patent_links(search_url)

        for pat in patent_links:
            patent_id = extract_patent_id_from_url(pat)
            output_dir = Path(f"data/patents/{patent_id}")

            if output_dir.exists():
                print(f"Pasta {output_dir} já existe. Pulando extração.")
                continue

            # Salvar as tabelas de dados
            saved_tables = save_raw_tables_from_html(pat, desired_compounds)

            # Se pelo menos uma tabela foi salva, salvar metadados e criar o diretório
            if saved_tables > 0:
                output_dir.mkdir(parents=True, exist_ok=True)
                metadata_file_path = output_dir / "metadata.txt"
                with open(metadata_file_path, "w") as metadata_file:
                    metadata_file.write(f"Patent URL: {pat}\n")
                    metadata_file.write(f"Page Max: {args.page_max}\n")
                    metadata_file.write(f"Keyword: {args.keyword}\n")
                print(f"Metadados salvos em '{metadata_file_path}'.")

            else:
                print(f"Nenhuma tabela foi salva para a patente {patent_id}. Metadados não foram gerados.")
