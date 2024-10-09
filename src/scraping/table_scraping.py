import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def extract_patent_id_from_url(url):
    # Extrai o ID da patente da URL (última parte após a "/")
    return url.split("/")[-1].split(".")[0]


def save_raw_tables_from_html(url):
    try:
        # Acessa a página da patente
        response = requests.get(url)
        response.raise_for_status()

        # Faz o parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.content, "html.parser")

        # Encontra a tag <patent-tables>
        patent_tables = soup.find("patent-tables")

        if patent_tables:
            # Encontra todas as tabelas dentro de <patent-tables>
            tables = patent_tables.find_all("table")
            raw_tables_html = []

            # Armazena cada tabela crua como HTML
            for table in tables:
                raw_tables_html.append(str(table))  # Armazena a tabela como HTML

            # Estrutura do JSON a ser salvo
            patent_data = {"url": url, "tables": raw_tables_html}

            # Cria o diretório usando pathlib
            output_dir = Path("data/patents/")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Extrai o ID da patente da URL e salva o arquivo com esse nome
            patent_id = extract_patent_id_from_url(url)
            json_file_path = output_dir / f"{patent_id}_tables.json"

            # Salva os dados no formato JSON
            with open(json_file_path, "w") as json_file:
                json.dump(patent_data, json_file, indent=4)

            print(f"Tabelas cruas extraídas com sucesso e salvas em '{json_file_path}'.")
        else:
            print("Elemento '<patent-tables>' não encontrado na página.")

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página: {e}")


def get_patent_links(search_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Encontrar links de patentes cujo texto contenha a palavra "glass"
    links = []
    for link in soup.find_all("a", href=True):
        # Verifica se o texto do link contém "glass" (não sensível a maiúsculas/minúsculas)
        if "glass" in link.get_text().lower():
            full_url = f"https://www.freepatentsonline.com{link['href']}"
            links.append(full_url)

    return links


# Configuração para buscar múltiplas páginas de patentes
page_max = 2

for page in range(1, page_max):
    search_url = (
        f"https://www.freepatentsonline.com/result.html?"
        f"p={page}&sort=relevance&srch=top&"
        f"query_txt=glass+composition&patents_us=on"
    )

    patent_links = get_patent_links(search_url)

    for pat in patent_links:
        patent_id = extract_patent_id_from_url(pat)
        json_file_path = Path(f"data/patents/{patent_id}_tables.json")

        # Verifica se o arquivo já existe
        if not json_file_path.exists():
            save_raw_tables_from_html(pat)
        else:
            print(f"Arquivo {json_file_path} já existe. Pulando extração.")
