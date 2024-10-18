import requests
from bs4 import BeautifulSoup


def search_patent_links_by_keyword_and_page(keyword, page):
    search_url = (
        f"https://www.freepatentsonline.com/result.html?"
        f"p={page}&sort=relevance&srch=top&query_txt={keyword}&patents_us=on"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    all_links = soup.find_all("a", href=True)

    links = [
        {
            "id": link["href"].replace("/", "_").replace(".html", ""),
            "title": link.get_text().lower(),
            "link": f"https://www.freepatentsonline.com{link['href']}",
        }
        for link in all_links
        if "glass" in link.get_text().lower()
    ]

    return links
