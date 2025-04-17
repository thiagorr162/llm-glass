import csv
import json
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup


def normalize_string(s):
    """
    Normalizes a string by removing accents, extra spaces, and converting to lowercase.
    """
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower())


def html_table_to_list(table):
    """
    Converts an HTML table to a list of lists (rows and columns).
    """
    return [
        [col.get_text(strip=True) for col in row.find_all("td")]
        for row in table.find_all("tr")
        if row.find_all("td")  # Only add rows with valid columns
    ]


# Load desired compounds from the JSON file
properties_file = Path("json/properties.json")
try:
    with properties_file.open(encoding="utf-8") as f:
        properties_data = json.load(f)
        desired_compounds = [normalize_string(compound) for compound in properties_data.get("desired_compounds", [])]
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading properties.json file: {e}")
    desired_compounds = []

# Path to the JSON folder
json_folder = Path("data/patents")

# Counters
good_tables_count = 0
bad_tables_count = 0
unsaved_tables_count = 0

# Iterate over all JSON files
for json_file in json_folder.rglob("*.json"):
    try:
        with json_file.open(encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading file {json_file.name}: {e}")
        continue

    # Check if there are tables in the "html_tables" field
    if not data.get("html_tables"):
        continue

    # Process each block of tables in the JSON
    for idx, patent_tables in enumerate(data["html_tables"], start=1):
        soup = BeautifulSoup(patent_tables, "html.parser")
        patent_table_elements = soup.find_all("patent-tables")

        if len(patent_table_elements) > 1:
            print(f"More than one <patent-tables> tag found in file {json_file.name}")

        # Process the first (and possibly only) <patent-tables> tag
        if not patent_table_elements:
            print(f"No <patent-tables> tag found in file {json_file.name}")
            continue

        patent_table = patent_table_elements[0]
        table_data = html_table_to_list(patent_table)

        # Check if the table contains desired compounds
        contains_desired = any(
            any(desired in normalize_string(cell) for desired in desired_compounds)
            for row in table_data
            for cell in row
        )

        if contains_desired:
            good_tables_count += 1
        else:
            bad_tables_count += 1

        # Create output folders
        output_folder = json_file.parent / "tables" / ("good_tables" if contains_desired else "bad_tables")
        output_folder.mkdir(parents=True, exist_ok=True)

        # CSV file name
        output_file = output_folder / f"{json_file.stem}-table_{idx}.csv"

        # Save the table as CSV
        try:
            with output_file.open(mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=",")
                writer.writerows(table_data)
            print(f"Table saved to {output_file}")
        except IOError as e:
            unsaved_tables_count += 1
            print(f"Error saving file {output_file.name}: {e}")

# Final report
print("\nSummary:")
print(f"Good tables saved: {good_tables_count}")
print(f"Bad tables saved: {bad_tables_count}")
print(f"Tables failed to save: {unsaved_tables_count}")
print("Operation completed successfully.")
