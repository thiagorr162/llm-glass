import json
import pathlib
import re
import unicodedata
import shutil
import csv

# ------------------------------------------------------------------------------
# 1. Helper functions
# ------------------------------------------------------------------------------

def normalize_string(s: str) -> str:
    """
    Normalize the input string by removing diacritics, collapsing whitespace,
    converting to ASCII, and lowercasing. This yields a canonical form suitable
    for comparing or searching text regardless of accents or spacing.
    """
    return re.sub(
        r"\s+",
        "",
        unicodedata.normalize("NFKD", s)
                   .encode("ASCII", "ignore")
                   .decode("utf-8")
                   .lower()
    )

molar_regex = re.compile(r'(?i)mol')
massic_keywords = [
    "wt %",
    "mass %",
    "mass percentage",
    "weight %",
    "weight percentage",
    "wt%",
    "wt-%",
    "wt.%", 
    "mass%",
]
massic_norm = [normalize_string(k) for k in massic_keywords]

def basis_type(table_text: str) -> str:
    """
    Determine the concentration basis of the provided table text.
    Returns:
        - "molar" if only molar units are detected,
        - "massic" if only mass-based units are detected,
        - "both" if both unit types appear,
        - "none" if no units are found.
    """
    text_norm   = normalize_string(table_text)
    found_molar = bool(molar_regex.search(text_norm))
    found_mass  = any(keyword in text_norm for keyword in massic_norm)

    if found_molar and not found_mass:
        return "molar"
    if found_mass and not found_molar:
        return "massic"
    if found_molar and found_mass:
        return "both"
    return "none"

def check_if_desired(text: str) -> bool:
    """
    Returns True if the normalized text contains any compound listed in
    the global variable `desired_compounds`, indicating the table snippet is relevant.
    """
    normalized = normalize_string(text)
    return any(compound in normalized for compound in desired_compounds)

# ------------------------------------------------------------------------------
# 2. Path configuration
# ------------------------------------------------------------------------------

input_path         = pathlib.Path("data/patents")                 
properties_file    = pathlib.Path("json/properties.json")         
not_splitted_path  = input_path / "not_splitted"                  
classification_csv = pathlib.Path("data/filtered/classifications.csv")

not_splitted_path.mkdir(parents=True, exist_ok=True)
classification_csv.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# 3. Clean Up Artifacts from Previous Runs
# ------------------------------------------------------------------------------

for d in input_path.glob("**/processed/splitted"):
    shutil.rmtree(d)                                              

if classification_csv.exists():
    classification_csv.unlink()                                   

# ------------------------------------------------------------------------------
# 4. Load Desired Compounds for Relevance Filtering
# ------------------------------------------------------------------------------

with properties_file.open(encoding="utf-8") as f:
    props = json.load(f)
desired_compounds = [normalize_string(c) for c in props.get("desired_compounds", [])]

# ------------------------------------------------------------------------------
# 5. Main Processing Loop: Iterate Over Extracted Good Tables
# ------------------------------------------------------------------------------

# --- open the classification CSV once, write header up-front ---
with classification_csv.open("w", encoding="utf-8", newline="") as cf:
    writer = csv.writer(cf)
    writer.writerow(["type", "IDS"])

    for table_file in input_path.rglob("good_tables/*.csv"):
        try:
            patent_dir = table_file.parents[2]
            json_file  = patent_dir / f"{patent_dir.name}.json"

            # 5.1 Extract Base Concentration Basis from JSON if Available
            json_basis = "none"
            if json_file.exists():
                with json_file.open(encoding="utf-8") as jf:
                    pat = json.load(jf)
                tables = pat.get("html_tables", [])
                if isinstance(tables, list) and tables:
                    html_concat = "\n".join(tables)
                    json_basis  = basis_type(html_concat)
            print(f"[DEBUG] Patent {patent_dir.name} json_basis = {json_basis!r}")

            overrides = 0

            # 5.2 Prepare output directory for split snippets
            output_path = patent_dir / "processed" / "splitted"
            output_path.mkdir(parents=True, exist_ok=True)

            # 5.3 Load the raw table text and identify relevant sub-sections
            txt = (
                table_file.read_text(encoding="utf-8")
                .replace('""', "")
                .replace(",,", ",-,")
            )
            raw = txt.split("\n\n")
            valid = [block for block in raw if check_if_desired(block)]

            # Handle multiple examples in one block
            glass_examples = []
            for block in valid:
                parts = (
                    block.lower().split("exemp")
                    if block.lower().count("exemp") > 1
                    else [block]
                )
                glass_examples.extend(p for p in parts if check_if_desired(p))

            if not glass_examples:
                dest = not_splitted_path / table_file.name
                shutil.copy(table_file, dest)
                print(f"No relevant compounds → moved {table_file.name}")
                continue

            # 5.4 Write each snippet to its own CSV, classify, and record result
            for idx, snippet in enumerate(glass_examples):
                filename = (
                    f"{table_file.stem}-{idx}.csv"
                    if len(glass_examples) > 1
                    else f"{table_file.stem}.csv"
                )
                out_path = output_path / filename

                cleaned_lines = "\n".join(
                    line for line in snippet.splitlines() if line.count(",") > 1
                )
                out_path.write_text(cleaned_lines, encoding="utf-8")

                snippet_basis = basis_type(snippet)
                final_basis   = (
                    json_basis
                    if snippet_basis == "none" and json_basis in ("molar", "massic")
                    else snippet_basis
                )
                overrides    += (final_basis != snippet_basis)

                writer.writerow([final_basis, str(out_path)])

            print(f"[DEBUG] Overrides for {patent_dir.name}: {overrides}")
            print(f"Processed → {output_path}")

        except Exception as e:
            dest = not_splitted_path / table_file.name
            shutil.copy(table_file, dest)
            print(f"Error {table_file.name}: {e} → moved")

# ------------------------------------------------------------------------------
# 6. Produce end-of-run statistics
# ------------------------------------------------------------------------------

counts = {"molar": 0, "massic": 0, "both": 0, "none": 0}
total  = 0

if classification_csv.exists():
    with classification_csv.open(encoding="utf-8") as cf:
        reader = csv.reader(cf)
        next(reader, None)
        for row in reader:
            category = row[0].lower()
            if category in counts:
                counts[category] += 1
            total += 1

    print("\nFinal classification summary:")
    for category, count in counts.items():
        pct = (count / total * 100.0) if total else 0.0
        print(f"{category}: {count} ({pct:.2f}%)")
else:
    print("No classifications generated.")

print("Operation completed successfully.")