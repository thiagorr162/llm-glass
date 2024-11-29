import argparse
import json
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# python src/scraping/get_patent_info.py -c {country} -p {n_pages} 

parser = argparse.ArgumentParser(
    description="Busca de patentes no Google Patents com base em palavras-chave e número de páginas."
)

parser.add_argument(
    "--pages",
    "-p",
    type=int,
    default=2,
    help="Número de páginas para procurar (default: 2)",
)
parser.add_argument(
    "--wait",
    "-w",
    type=int,
    default=3,
    help="Seconds to wait to load patents.",
)
parser.add_argument(
    "--keywords",
    "-k",
    nargs="+",
    default=["glass", "refractive"],
    help="Lista de palavras-chave para busca (default: ['glass', 'refractive'])",
)
parser.add_argument(
    "--country",
    "-c",
    type=str,
    default=None,
    help="Country to get patents. (default: None, get patent for any country.)",
)
parser.add_argument(
    "--selenium_path",
    type=str,
    default="src/scraping/geckodriver.exe",
    help="Path to selenium driver.",
)

args = parser.parse_args()

keywords = args.keywords
pages = args.pages

country = args.country

all_urls = []

geckodriver_path = args.selenium_path
service = Service(executable_path=geckodriver_path)

firefox_binary_path = "C:/Program Files/Mozilla Firefox/firefox.exe"  
options = Options()
options.binary = firefox_binary_path

browser = webdriver.Firefox(service=service, options=options)

for page in range(0, pages + 1):
    print(f"Getting links for page: {page}")

    search_url = (
        "https://patents.google.com/?q=" + "&q=".join([f"TI%3d({keyword})" for keyword in keywords]) + "&sort=new"
    )
    search_url = search_url + "&sort=new"
    search_url = search_url + f"&page={page}"

    if args.country is not None:
        country = country.upper()
        search_url = search_url + f"&country={country}"

    browser.get(search_url)

    wait = WebDriverWait(browser, args.wait)

    patent_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "search-result-item")))

    for patent in patent_elements:
        state_modifier = patent.find_element(By.CSS_SELECTOR, "state-modifier")
        data_result = state_modifier.get_attribute("data-result")
        full_url = "https://patents.google.com/" + data_result
        all_urls.append(full_url)

print("All links done!\n")

output_dir = Path("data/patents")
output_dir.mkdir(parents=True, exist_ok=True)

for url in all_urls:
    file_name = url.replace("https://", "").replace(".", "_").replace("/", "_")

    output_path = output_dir / file_name
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / (file_name + ".json")

    if output_file.exists():
        print(f"Arquivo {output_file} já existe. Pulando a criação.")
        continue

    browser.get(url)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def get_meta_content(selector):
        elements = browser.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            result = [element.get_attribute("content").strip() for element in elements]
            if len(result) == 1:
                return result[0]
            else:
                return result
        return None

    title = get_meta_content("meta[name='DC.title']")
    patent_type = get_meta_content("meta[name='DC.type']")
    description = get_meta_content("meta[name='DC.description']")
    application_number = get_meta_content("meta[name='citation_patent_application_number']")
    publication_number = get_meta_content("meta[name='citation_patent_publication_number']")
    pdf_url = get_meta_content("meta[name='citation_pdf_url']")

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

    with output_file.open(mode="w", encoding="utf-8") as f:
        json.dump(patent_data, f, ensure_ascii=False, indent=4)

browser.quit()

