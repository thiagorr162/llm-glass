import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup
from tqdm import tqdm


def normalize_string(s):
    """
    Normalize a string by removing accents, extra whitespace, and converting to lowercase.
    This helps standardize text for reliable comparison and matching.

    Steps:
    1. Apply Unicode NFKD normalization to decompose accented characters.
    2. Encode to ASCII bytes, ignoring non-ASCII components (removes accents).
    3. Decode back to UTF-8 text.
    4. Convert all letters to lowercase.
    5. Remove any remaining whitespace characters.
    """
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())


# TODO: não sei se isso é necessário, mas nao vou tirar agora pq pode quebrar tudo
def html_table_to_list(table):
    """
    Convert an HTML <table> element into a list of rows, where each row is a list of text values.

    Only <tr> elements containing <td> cells are processed. Empty or header-only rows are skipped.
    """
    return [
        [col.get_text(strip=True) for col in row.find_all("td")] for row in table.find_all("tr") if row.find_all("td")
    ]


properties_file = Path("json/desired_compounds.json")

with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [compound.lower() for compound in properties_data]

# Define the directory containing patent JSON files
json_folder = Path("data/patents/metadata")

# Recursively search for all JSON files under the patents directory
json_files = json_folder.rglob("*.json")


for json_file in tqdm(json_files):
    with json_file.open(encoding="utf-8") as f:
        data = json.load(f)

    for idx, patent_tables in enumerate(data["html_tables"], start=1):
        # Parse the HTML content for table extraction
        soup = BeautifulSoup(patent_tables, "html.parser")
        patent_table_elements = soup.find_all("patent-tables")

        if not patent_table_elements:
            continue

        assert len(patent_table_elements) == 1, "patent_table_elements has more than 1 element"

        patent_table = patent_table_elements[0]

        table_data = html_table_to_list(patent_table)

        # Check if any cell in the table matches one of the desired compounds
        contains_desired = any(
            any(desired in normalize_string(cell) for desired in desired_compounds)
            for row in table_data
            for cell in row
        )

        output_folder = json_file.parent
        output_folder = Path(str(output_folder).replace("/metadata/", "/individual_tables/"))

        tables_folder = output_folder / ("compounds" if contains_desired else "not_compounds")

        tables_folder.mkdir(parents=True, exist_ok=True)

        html_file = tables_folder / f"{json_file.stem}-table_{idx}.html"
        html_file.write_text(str(patent_table), encoding="utf-8")

    # Save original JSON data
    json_copy = output_folder / f"{json_file.stem}-original.json"
    json_copy.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


print("Operation completed successfully.")
