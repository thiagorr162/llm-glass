from selenium import webdriver

# Definindo as palavras-chave
keywords = [
    "glass",
    "refractive",
    "table",
]

# Construindo a URL de busca com múltiplos parâmetros de consulta
search_url = "https://patents.google.com/?q=" + "&q=".join(keywords)
search_url = search_url + "&sort=new"

breakpoint()
geckodriver_path = "/usr/local/bin/geckodriver"
driver_service = webdriver.FirefoxService(executable_path=geckodriver_path)

browser = webdriver.Firefox(service=driver_service)


browser.get(search_url)
