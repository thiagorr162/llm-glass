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

# python src/scraping/get_patent_info.py -p {n_pages} -w {wait} -k {keywords} -c {country} -r {results_number}

parser = argparse.ArgumentParser(
    description="Patent search on Google Patents based on keywords and page numbers."
)

parser.add_argument(
    "--pages",
    "-p",
    type=int,
    default=2,
    help="Number of pages to search (default: 2)",
)
parser.add_argument(
    "--wait_time",  
    "-w",
    type=int,
    default=0,
    help="Seconds to wait after the patent has loaded(default: 0)",
)
parser.add_argument(
    "--keywords",
    "-k",
    nargs="+",
    default=["glass", "refractive"],
    help="List of keywords for search (default: ['glass', 'refractive'])",
)
parser.add_argument(
    "--country",
    "-c",
    type=str,
    default=None,
    help="Country to search for patents (default: None, search in any country).",
)
parser.add_argument(
    "--selenium_path",
    type=str,
    default="src/scraping/geckodriver.exe",
    help="Path to the Selenium driver.",
)
parser.add_argument(
    "--results",
    "-r",
    type=int,
    default=100,
    help="Number of results per page in the search (default: 100)",
)

args = parser.parse_args()
results = args.results
keywords = args.keywords
pages = args.pages
country = args.country
wait_time = args.wait_time  
all_urls = []

geckodriver_path = args.selenium_path
service = Service(executable_path=geckodriver_path)

firefox_binary_path = "C:/Program Files/Mozilla Firefox/firefox.exe"
options = Options()
options.binary = firefox_binary_path

browser = webdriver.Firefox(service=service, options=options)

def construct_search_url(keywords, page, results, country=None):
    base_url = "https://patents.google.com/?q="
    keyword_query = "&q=".join([f"({keyword})" for keyword in keywords])
    url = f"{base_url}{keyword_query}&num={results}&page={page}"
    if country:
        url += f"&country={country.upper()}"
    return url

# Loading URLs from the file
with open('C:/Users/thoma/Downloads/urls_eric.txt', 'r') as file:
    all_urls = [linha.strip() for linha in file]

output_dir = Path("data/patents")
output_dir.mkdir(parents=True, exist_ok=True)

for url in all_urls:
    file_name = url.replace("https://", "").replace(".", "_").replace("/", "_")

    output_path = output_dir / file_name
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / (file_name + ".json")

    if output_file.exists():
        print(f"File {output_file} already exists. Skipping creation.")
        continue

    browser.get(url)
    wait = WebDriverWait(browser, timeout=wait_time, poll_frequency=0.5)
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

print("Operation completed successfully.") 