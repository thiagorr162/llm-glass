import requests
from bs4 import BeautifulSoup


def get_patent_links(search_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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

page=1
search_url = f"https://www.freepatentsonline.com/result.html?p={page}&sort=relevance&srch=top&query_txt=glass+composition&patents_us=on"

patent_links = get_patent_links(search_url)

breakpoint()
