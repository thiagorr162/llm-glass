import csv
import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup


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
breakpoint()

# Define the directory containing patent JSON files
json_folder = Path("data/patents")

# Recursively search for all JSON files under the patents directory
json_files = list(json_folder.rglob("*.json"))
print(f"Found {len(json_files)} JSON files.")

# Recursively search for all JSON files under the patents directory
for json_file in json_files:
    with json_file.open(encoding="utf-8") as f:
        data = json.load(f)

    for idx, patent_tables in enumerate(data["html_tables"], start=1):
        # Parse the HTML content for table extraction
        breakpoint()
        soup = BeautifulSoup(patent_tables, "html.parser")
        patent_table_elements = soup.find_all("patent-tables")

        # Warn if multiple <patent-tables> tags are found
        if len(patent_table_elements) > 1:
            print(f"Multiple <patent-tables> tags found in {json_file.name}")
        # Skip if no <patent-tables> tag is present
        if not patent_table_elements:
            print(f"No <patent-tables> tag found in {json_file.name}")
            continue

        # Use only the first <patent-tables> element for table conversion
        patent_table = patent_table_elements[0]
        table_data = html_table_to_list(patent_table)

        # Check if any cell in the table matches one of the desired compounds
        contains_desired = any(
            any(desired in normalize_string(cell) for desired in desired_compounds)
            for row in table_data
            for cell in row
        )

        # Create an output directory under the JSON file's parent:
        # 'good_tables' if table contains desired compounds, otherwise 'bad_tables'
        output_folder = json_file.parent / "tables" / ("good_tables" if contains_desired else "bad_tables")
        output_folder.mkdir(parents=True, exist_ok=True)

        # Construct the output CSV filename including the table index
        output_file = output_folder / f"{json_file.stem}-table_{idx}.csv"

        try:
            # Write the extracted table rows to a CSV file
            with output_file.open(mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=",")
                writer.writerows(table_data)
            print(f"Table saved to: {output_file}")
        except IOError as e:
            print(f"Error saving file {output_file.name}: {e}")

print("Operation completed successfully.")
