import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

page = 5

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
wait = WebDriverWait(browser, 15)

# Localizar os elementos que contêm as patentes
patent_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "search-result-item")))

all_urls = []

# Capturar os URLs das patentes
for patent in patent_elements:
    state_modifier = patent.find_element(By.CSS_SELECTOR, "state-modifier")
    data_result = state_modifier.get_attribute("data-result")
    full_url = "https://patents.google.com/" + data_result
    all_urls.append(full_url)


for url in all_urls:
    print(url + "\n\n\n\n\n\n\n\n")
    # Navegar para a URL completa da patente
    browser.get(url)

    # Esperar até que a nova página de patente seja carregada
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Tempo de espera adicional para garantir que a página esteja totalmente carregada
    time.sleep(2)

    # Função auxiliar para verificar a existência de elementos
    def get_meta_content(selector):
        elements = browser.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            return elements[0].get_attribute("content")
        return None

    # Capturar os dados com base na presença dos elementos
    title = get_meta_content("meta[name='DC.title']")
    patent_type = get_meta_content("meta[name='DC.type']")
    description = get_meta_content("meta[name='DC.description']")
    application_number = get_meta_content("meta[name='citation_patent_application_number']")
    publication_number = get_meta_content("meta[name='citation_patent_publication_number']")
    pdf_url = get_meta_content("meta[name='citation_pdf_url']")

    # Para inventores, retornar uma lista de nomes
    inventors = [
        element.get_attribute("content")
        for element in browser.find_elements(By.CSS_SELECTOR, "meta[scheme='inventor']")
    ] or None
    assignee = get_meta_content("meta[scheme='assignee']")
    date = get_meta_content("meta[name='DC.date']")

    # Imprimir os dados coletados
    print(f"URL: {url}")
    print(f"Título: {title}")
    print(f"Tipo: {patent_type}")
    print(f"Descrição: {description}")
    print(f"Número de Aplicação: {application_number}")
    print(f"Número de Publicação: {publication_number}")
    print(f"PDF URL: {pdf_url}")
    print(f"Inventores: {', '.join(inventors) if inventors else None}")
    print(f"Assignee: {assignee}")
    print(f"Data: {date}")
    print("=" * 50)

# Fechar o navegador ao final (se necessário)
browser.quit()
