import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def extract_patent_id_from_url(url):
    # Extrai o ID da patente da URL (última parte após a "/")
    return url.split("/")[-1].split(".")[0]


def format_table_as_text(table):
    # Formata a tabela em HTML como um texto com separador de vírgula
    rows = table.find_all("tr")  # Encontra todas as linhas da tabela
    table_text = []

    for row in rows:
        columns = row.find_all(["th", "td"])  # Encontra todas as células
        row_text = [col.get_text(strip=True) for col in columns]  # Extrai o texto de cada célula
        # Junta as células da linha com separação por vírgula
        table_text.append(",".join(row_text))

    # Junta todas as linhas da tabela, separadas por quebras de linha
    return "\n".join(table_text)


def contains_desired_compounds(table_text, desired_compounds):
    # Verifica se pelo menos um dos compostos desejados está presente no texto da tabela
    return any(compound in table_text for compound in desired_compounds)


def save_raw_tables_from_html(url, desired_compounds):
    try:
        # Acessa a página da patente
        # url = "https://www.freepatentsonline.com/9957191.html"  # Mantida aqui como exemplo para teste
        response = requests.get(url)
        response.raise_for_status()

        # Faz o parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.content, "html.parser")

        # Encontra a tag <table>
        tables = soup.find_all("table")

        # Inicializa um contador de tabelas salvas
        saved_tables = 0

        if tables:
            # Converte cada tabela para texto formatado e salva se contiver compostos desejados
            for idx, table in enumerate(tables, start=1):
                table_text = format_table_as_text(table)  # Converte a tabela para texto formatado

                if contains_desired_compounds(table_text, desired_compounds):
                    # Apenas cria a pasta se for necessário salvar a tabela
                    if saved_tables == 0:
                        patent_id = extract_patent_id_from_url(url)
                        output_dir = Path(f"data/patents/{patent_id}")
                        output_dir.mkdir(parents=True, exist_ok=True)

                    table_file_path = output_dir / f"table_{idx}.txt"

                    # Salva o texto formatado da tabela no arquivo .txt
                    with open(table_file_path, "w") as table_file:
                        table_file.write(table_text)

                    print(f"Tabela {idx} salva em '{table_file_path}'.")
                    saved_tables += 1

            if saved_tables == 0:
                print("Nenhuma tabela contém compostos desejados. Nenhum arquivo foi salvo.")
        else:
            print("Elemento '<table>' não encontrado na página.")

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


# Leitura dos compostos desejados a partir do arquivo JSON
with open("json/properties.json", "r") as json_file:
    data = json.load(json_file)
    desired_compounds = data["desired_compounds"]

# Configuração para buscar múltiplas páginas de patentes
page_max = 1

for page in range(1, page_max + 1):
    search_url = (
        f"https://www.freepatentsonline.com/result.html?"
        f"p={page}&sort=relevance&srch=top&"
        f"query_txt=glass+composition&patents_us=on"
    )

    patent_links = get_patent_links(search_url)

    for pat in patent_links:
        patent_id = extract_patent_id_from_url(pat)
        output_dir = Path(f"data/patents/{patent_id}")

        # Verifica se o diretório da patente já existe
        if not output_dir.exists():
            save_raw_tables_from_html(pat, desired_compounds)
        else:
            print(f"Pasta {output_dir} já existe. Pulando extração.")
