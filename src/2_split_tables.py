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

        normalized_rows = [[normalize_string(cell) for cell in row] for row in rows]

        if not normalized_rows:
            continue

        df_raw = pd.DataFrame(normalized_rows).T

        # Detecta a linha de início (a que tem >= 2 compostos desejados)
        start_index = None
        for idx, row in df_raw.iterrows():
            count = sum(any(comp in str(cell) for comp in desired_compounds) for cell in row)
            if count >= 2:
                start_index = idx
                break

        if start_index is not None:
            header = df_raw.iloc[start_index].tolist()
            data = df_raw.iloc[start_index+1:]

            df = pd.DataFrame(data.values, columns=header)

            df["patent_id"] = f"{file.stem}_block_{i}"

            df = df.apply(lambda col: col.map(normalize_string))

            output_folder = Path(str(file.parent).replace("/has_compounds", "/splited/"))
            output_folder.mkdir(parents=True, exist_ok=True)

            output_path = output_folder / f"{file.stem}_block_{i}.csv"
            df.to_csv(output_path, index=False, header=True)
