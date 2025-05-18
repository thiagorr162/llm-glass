from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

tables_folder = Path("data/patents/processing")
html_files = tables_folder.rglob("*.html")

for file in tqdm(html_files):
    with open(file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    fragments = soup.prettify().split("colspan")

    for i, fragment in enumerate(fragments):
        frag_soup = BeautifulSoup(fragment, "html.parser")

        rows = []
        for tr in frag_soup.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)

        if rows:
            df = pd.DataFrame(rows)

            # Define pasta de saída com base na estrutura original
            output_folder = Path(str(file.parent).replace("/has_compounds", "/splited/"))
            output_folder.mkdir(parents=True, exist_ok=True)

            output_path = output_folder / f"{file.stem}_block_{i}.csv"
            df.to_csv(output_path, index=False, header=False)
