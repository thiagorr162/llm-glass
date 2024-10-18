from src.utils.scraping_utils import search_patent_links_by_keyword_and_page

page = 1
keyword = "glass refractive"

links = search_patent_links_by_keyword_and_page(keyword, page)

breakpoint()
