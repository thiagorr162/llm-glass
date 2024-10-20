import json
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

page = 2

keywords = [
    "glass",
    "refractive",
]

# Construindo a URL de busca com múltiplos parâmetros de consulta
search_url = "https://patents.google.com/?q=" + "&q=".join([f"TI%3d({keyword})" for keyword in keywords]) + "&sort=new"
search_url = search_url + "&sort=new"
search_url = search_url + f"&page={page}"

geckodriver_path = "/usr/local/bin/geckodriver"
driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)

browser = webdriver.Firefox(service=driver_service)

browser.get(search_url)

# Definir um tempo de espera até que os resultados estejam disponíveis
wait = WebDriverWait(browser, 10)

# Localizar os elementos que contêm as patentes
patent_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "search-result-item")))

all_urls = []

# Capturar os URLs das patentes
for patent in patent_elements:
    state_modifier = patent.find_element(By.CSS_SELECTOR, "state-modifier")
    data_result = state_modifier.get_attribute("data-result")
    full_url = "https://patents.google.com/" + data_result
    all_urls.append(full_url)

# Criar o diretório data/patents se ele não existir
output_dir = Path("data/patents")
output_dir.mkdir(parents=True, exist_ok=True)

for url in all_urls:
    file_name = url.replace("https://", "").replace(".", "_").replace("/", "_") + ".json"
    output_file = output_dir / file_name

    # Verificar se o arquivo já existe
    if output_file.exists():
        print(f"Arquivo {output_file} já existe. Pulando a criação.")
        continue

    # Navegar para a URL completa da patente
    browser.get(url)

    # Esperar até que a nova página de patente seja carregada
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Função auxiliar para verificar a existência de elementos
    def get_meta_content(selector):
        elements = browser.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            result = [element.get_attribute("content").strip() for element in elements]
            if len(result) == 1:
                return result[0]
            else:
                return result
        return None

    # Capturar os dados com base na presença dos elementos
    title = get_meta_content("meta[name='DC.title']")
    patent_type = get_meta_content("meta[name='DC.type']")
    description = get_meta_content("meta[name='DC.description']")
    application_number = get_meta_content("meta[name='citation_patent_application_number']")
    publication_number = get_meta_content("meta[name='citation_patent_publication_number']")
    pdf_url = get_meta_content("meta[name='citation_pdf_url']")

    # Para inventores, retornar uma lista de nomes
    inventors = get_meta_content("meta[scheme='inventor']")
    assignee = get_meta_content("meta[scheme='assignee']")
    date = get_meta_content("meta[name='DC.date']")

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "patent-tables table")))
        patent_tables = browser.find_elements(By.CSS_SELECTOR, "patent-tables")
        html_tables = []

        for table in patent_tables:
            patent_table_html = table.get_attribute("outerHTML")
            soup = BeautifulSoup(patent_table_html, "html.parser").prettify()

            html_tables.append(soup)
    except TimeoutException:
        print(f"No patent tables found on {url}.")
        html_tables = []

    # Criar um dicionário com os dados
    patent_data = {
        "url": url,
        "title": title,
        "type": patent_type,
        "description": description,
        "application_number": application_number,
        "publication_number": publication_number,
        "pdf_url": pdf_url,
        "inventors": inventors,
        "assignee": assignee,
        "date": date,
        "html_tables": html_tables,
    }

    # Gerar o nome do arquivo com base na URL (remover caracteres inválidos)

    # Salvar os dados em um arquivo JSON
    with output_file.open(mode="w", encoding="utf-8") as f:
        json.dump(patent_data, f, ensure_ascii=False, indent=4)


# Fechar o navegador ao final (se necessário)
browser.quit()
