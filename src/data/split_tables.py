#Esta versão é mais simples do que a versão final, mas ficará aqui para critério de ajustes, pois ela não lida com a classificaçã

import json
import pathlib
import re
import unicodedata
import shutil

# Function to normalize strings: removes spaces, accents, and converts to lowercase
def normalize_string(s):
    """Normalizes strings by removing accents, spaces, and converting to lowercase."""
    return re.sub(
        r"\s+", "",
        unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower()
    )

# Function to check if a text contains any desired compounds
def check_if_desired(text):
    """Checks if the text contains any desired compound."""
    normalized_text = normalize_string(text)
    return any(compound in normalized_text for compound in desired_compounds)

# Main paths
input_path = pathlib.Path("data/patents")  # Input path
properties_file = pathlib.Path("json/properties.json")  # JSON file with properties
not_splited_path = input_path / "not_splited"  # Folder for unsplit files
not_splited_path.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist

# Load desired compounds
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(c) for c in properties_data.get("desired_compounds", [])]

# Process each CSV file in the 'good_tables' folder
for table_file in input_path.rglob("*/good_tables/*.csv"):
    try:
        # Read the file content
        with table_file.open("r", encoding="utf-8") as f:
            txt_table = f.read()

        # Adjustments to the file text
        txt_table = txt_table.replace('""', "").replace(",,", ",-,")
        all_tables = txt_table.split("\n\n")  # Split by double newline

        # Filter tables with desired compounds
        correct_tables = [t for t in all_tables if check_if_desired(t)]
        glass_examples = []

        # Separate examples in the filtered tables
        for t in correct_tables:
            examples = t.lower().split("exemp") if t.lower().count("exemp") > 1 else [t]
            glass_examples.extend(ex for ex in examples if check_if_desired(ex))

        # Create output path
        output_path = table_file.parents[2] / "processed/splitted"
        output_path.mkdir(parents=True, exist_ok=True)

        if glass_examples:
            # Save the filtered tables
            for i, example in enumerate(glass_examples):
                output_file = output_path / f"{table_file.stem}-{i}.csv" if len(glass_examples) > 1 else output_path / f"{table_file.stem}.csv"
                filtered_lines = "\n".join(line for line in example.splitlines() if line.count(",") > 1)

                with output_file.open("w", encoding="utf-8") as file:
                    file.write(filtered_lines)
            print(f"File saved: {output_file}")

        else:
            # Copy problematic file to 'not_splited'
            destination = not_splited_path / table_file.name
            if destination.exists():
                parent_folder = table_file.parent.parent.name
                destination = not_splited_path / f"{table_file.stem}_{parent_folder}.csv"
            shutil.copy(table_file, destination)
            print(f"File without relevant tables copied to: {destination}")

    except Exception as e:
        # In case of error, copy to 'not_splited'
        destination = not_splited_path / table_file.name
        if destination.exists():
            parent_folder = table_file.parent.parent.name
            destination = not_splited_path / f"{table_file.stem}_{parent_folder}.csv"
        shutil.copy(table_file, destination)
        print(f"Error processing {table_file}: {e}. File copied to: {destination}")

# Indicate the completion of the operation
print("Operation completed successfully.")
