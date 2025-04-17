import json
import pathlib
import re
import unicodedata
import shutil
import csv

# HELPER FUNCTIONS

def normalize_string(s):
    """
    Normalizes a string by removing accents, spaces, and converting it to lowercase.
    """
    return re.sub(
        r"\s+",
        "",
        unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8").lower()
    )

# Regex pattern to match variations of "mol"
molar_regex = re.compile(r'(?i)mol')

# List of mass-based keywords
massic_keywords = [
    "wt %",
    "mass %", 
    "mass percentage", 
    "weight %", 
    "weight percentage", 
    "wt%", 
    "wt-%", 
    "wt.%", 
    "mass %", 
    "mass%"
]

# Pre-normalize keywords for efficient comparison
massic_norm = [normalize_string(k) for k in massic_keywords]

def basis_type(table_text):
    """
    Determines the concentration basis of a table: molar, massic, both, or none.
    Returns:
        - "molar" if molar keywords are found and no massic keywords,
        - "massic" if massic keywords are found and no molar keywords,
        - "both" if both are present,
        - "none" otherwise.
    """
    text_norm = normalize_string(table_text)
    found_molar_matches = molar_regex.findall(text_norm)
    found_molar = len(found_molar_matches) > 0
    found_massic = any(mk in text_norm for mk in massic_norm)

    if found_molar and not found_massic:
        print(found_molar_matches)
        return "molar"
    elif found_massic and not found_molar:
        print(found_massic)
        return "massic"
    elif found_molar and found_massic:
        print(found_massic)
        print(found_molar_matches)
        return "both"
    else:
        return "none"

def check_if_desired(text):
    """
    Checks whether the given text contains any of the desired compounds.
    """
    normalized_text = normalize_string(text)
    return any(compound in normalized_text for compound in desired_compounds)

# MAIN SCRIPT

# Define paths
input_path = pathlib.Path("data/patents")
properties_file = pathlib.Path("json/properties.json")
not_splitted_path = input_path / "not_splitted"
not_splitted_path.mkdir(parents=True, exist_ok=True)
classification_csv_path = pathlib.Path("data/filtered")
classification_csv_path.mkdir(parents=True, exist_ok=True)

# Clean up previous split directories
for splited_dir in input_path.glob("**/processed/splitted"):
    shutil.rmtree(splited_dir)

# Reset the classifications CSV file if it exists
classification_csv_file = classification_csv_path / "classifications.csv"
if classification_csv_file.exists():
    classification_csv_file.unlink()

# Load and normalize desired compounds
with properties_file.open(encoding="utf-8") as f:
    properties_data = json.load(f)
    desired_compounds = [normalize_string(c) for c in properties_data.get("desired_compounds", [])]

# Initialize counter for split tables
splitted_tables_count = 0

# Iterate over all CSV files in good_tables directories
for table_file in input_path.rglob("good_tables/*.csv"):
    try:
        # Define output path for split tables
        output_path = table_file.parents[2] / "processed/splitted"
        output_path.mkdir(parents=True, exist_ok=True)

        # Read the table content
        with table_file.open("r", encoding="utf-8") as f:
            txt_table = f.read()

        # Apply formatting fixes
        txt_table = txt_table.replace('""', "").replace(",,", ",-,")

        # Split by double newline to separate tables
        all_tables = txt_table.split("\n\n")

        # Filter tables that contain desired compounds
        correct_tables = [t for t in all_tables if check_if_desired(t)]
        glass_examples = []

        # Further split examples by "exemp" keyword if multiple occur
        for t in correct_tables:
            examples = t.lower().split("exemp") if t.lower().count("exemp") > 1 else [t]
            glass_examples.extend(ex for ex in examples if check_if_desired(ex))

        # Only proceed with classification if valid examples are found
        if glass_examples:
            classification_csv = classification_csv_path / "classifications.csv"
            for i, example in enumerate(glass_examples):
                # Define the output file name
                if len(glass_examples) > 1:
                    output_file = output_path / f"{table_file.stem}-{i}.csv"
                else:
                    output_file = output_path / f"{table_file.stem}.csv"

                # Filter valid CSV lines (with at least two commas)
                filtered_lines = "\n".join(
                    line for line in example.splitlines() if line.count(",") > 1
                )

                # Save the filtered snippet
                with output_file.open("w", encoding="utf-8") as file:
                    file.write(filtered_lines)
                splitted_tables_count += 1  # Increment split count

                # Append classification entry to CSV using the new splitted file name as ID
                with classification_csv.open("a", encoding="utf-8", newline="") as cf:
                    writer = csv.writer(cf)
                    if cf.tell() == 0:
                        writer.writerow(["type", "IDS"])
                    writer.writerow([basis_type(example), str(output_file)])
            print(f"File(s) saved to: {output_path}")

        else:
            # If no desired compounds found, move the file to not_splitted (no classification)
            destination = not_splitted_path / table_file.name
            if destination.exists():
                parent_folder = table_file.parent.parent.name
                destination = not_splitted_path / f"{table_file.stem}_{parent_folder}.csv"
            shutil.copy(table_file, destination)
            print(f"File without relevant compounds moved to: {destination}")

    except Exception as e:
        # On error, move the file to not_splitted and log the issue
        destination = not_splitted_path / table_file.name
        if destination.exists():
            parent_folder = table_file.parent.parent.name
            destination = not_splitted_path / f"{table_file.stem}_{parent_folder}.csv"
        shutil.copy(table_file, destination)
        print(f"Error processing {table_file}: {e}. File moved to: {destination}")

print("Operation completed successfully.")

# Final report with classification counts
counts = {"molar": 0, "massic": 0, "both": 0, "none": 0}
total = 0

classification_csv = classification_csv_path / "classifications.csv"
if classification_csv.exists():
    with classification_csv.open("r", encoding="utf-8") as cf:
        reader = csv.reader(cf)
        header = next(reader, None)  # Skip header
        for row in reader:
            type_val = row[0].strip().lower()
            if type_val in counts:
                counts[type_val] += 1
            total += 1

    print("\nFinal classification summary:")
    for key, count in counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{key}: {count} ({percentage:.2f}%)")

    print(f"\nTotal splitted tables generated: {splitted_tables_count}")
else:
    print("\nNo classification file generated (no desired compounds found).")
