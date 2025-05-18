import json
import unicodedata
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


def normalize_string(s):
    if s is None:
        return s
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


# Carrega compostos desejados e normaliza
with open("json/desired_compounds.json", "r", encoding="utf-8") as f:
    desired_compounds = json.load(f)

desired_compounds = [normalize_string(comp) for comp in desired_compounds]

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

        # Normaliza as strings nas linhas
        normalized_rows = [[normalize_string(cell) for cell in row] for row in rows]

        # Encontra o índice da primeira linha com algum composto desejado
        start_index = None
        for idx, row in enumerate(normalized_rows):
            if any(comp in cell for cell in row for comp in desired_compounds):
                start_index = idx
                break

        if start_index is not None:
            trimmed_rows = normalized_rows[start_index:]
            df = pd.DataFrame(trimmed_rows).T

            # Aplica normalização corretamente no DataFrame
            df = df.apply(lambda col: col.map(normalize_string))

            output_folder = Path(str(file.parent).replace("/has_compounds", "/splited/"))
            output_folder.mkdir(parents=True, exist_ok=True)

            output_path = output_folder / f"{file.stem}_block_{i}.csv"
            df.to_csv(output_path, index=False, header=False)
