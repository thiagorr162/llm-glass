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
    Return a lowercase, accent-free, whitespace-free version of *s*.
    This canonical form simplifies keyword detection regardless of
    diacritics or spacing variations.
    """
    return re.sub(
        r"\s+",
        "",
        unicodedata.normalize("NFKD", s)
                   .encode("ASCII", "ignore")
                   .decode("utf-8")
                   .lower()
    )

# Compiled pattern that matches any case variation of the substring “mol”.
molar_regex = re.compile(r'(?i)mol')

# Keywords that indicate a mass-based concentration; all are normalized below.
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
    Classify *table_text* as one of:
        • "molar"  – only molar indicators are present
        • "massic" – only mass indicators are present
        • "both"   – both molar and mass indicators are present
        • "none"   – no indicators detected
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
    Return True if *text* (normalized) contains at least one compound from
    *desired_compounds* (defined later from properties.json).
    """
    normalized = normalize_string(text)
    return any(compound in normalized for compound in desired_compounds)

# ------------------------------------------------------------------------------
# 2. Path configuration
# ------------------------------------------------------------------------------

input_path         = pathlib.Path("data/patents")                 # Root of patent data
properties_file    = pathlib.Path("json/properties.json")         # List of target compounds
not_splitted_path  = input_path / "not_splitted"                  # Tables skipped or errored
classification_csv = pathlib.Path("data/filtered/classifications.csv")

# Ensure output directories exist
not_splitted_path.mkdir(parents=True, exist_ok=True)
classification_csv.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# 3. House-keeping: remove artefacts from previous runs
# ------------------------------------------------------------------------------

for d in input_path.glob("**/processed/splitted"):
    shutil.rmtree(d)                                              # Purge old split folders
if classification_csv.exists():
    classification_csv.unlink()                                   # Remove old summary CSV

# ------------------------------------------------------------------------------
# 4. Load list of compounds that qualify a table as “relevant”
# ------------------------------------------------------------------------------

with properties_file.open(encoding="utf-8") as f:
    props = json.load(f)
desired_compounds = [normalize_string(c) for c in props.get("desired_compounds", [])]

# ------------------------------------------------------------------------------
# 5. Main loop – scan every CSV produced by the HTML parser
# ------------------------------------------------------------------------------

for table_file in input_path.rglob("good_tables/*.csv"):
    try:
        patent_dir = table_file.parents[2]                        # Patent root directory
        json_file  = patent_dir / f"{patent_dir.name}.json"       # Patent metadata JSON

        # ----------------------------------------------------------------------
        # 5.1 Derive a fallback basis from the concatenated HTML tables
        # ----------------------------------------------------------------------
        json_basis = "none"
        if json_file.exists():
            with json_file.open(encoding="utf-8") as jf:
                pat = json.load(jf)
            tables = pat.get("html_tables", [])
            if isinstance(tables, list) and tables:
                html_concat = "\n".join(tables)                   # Combine all HTML snippets
                json_basis  = basis_type(html_concat)
        print(f"[DEBUG] Patent {patent_dir.name} json_basis = {json_basis!r}")

        overrides = 0                                             # Counter for later reporting

        # ----------------------------------------------------------------------
        # 5.2 Prepare output directory for split snippets
        # ----------------------------------------------------------------------
        output_path = patent_dir / "processed" / "splitted"
        output_path.mkdir(parents=True, exist_ok=True)

        # ----------------------------------------------------------------------
        # 5.3 Load the raw table text and identify relevant sub-sections
        # ----------------------------------------------------------------------
        txt = table_file.read_text(encoding="utf-8") \
                       .replace('""', "") \
                       .replace(",,", ",-,")                       # Remove artefacts from CSV export
        raw = txt.split("\n\n")                                   # Block-level split
        valid = [block for block in raw if check_if_desired(block)]

        # Some files embed multiple “example” sections; split on “exemp”
        glass_examples = []
        for block in valid:
            parts = block.lower().split("exemp") \
                    if block.lower().count("exemp") > 1 else [block]
            glass_examples.extend(p for p in parts if check_if_desired(p))

        # If no desired compounds are found, move file for manual inspection
        if not glass_examples:
            dest = not_splitted_path / table_file.name
            shutil.copy(table_file, dest)
            print(f"No relevant compounds → moved {table_file.name}")
            continue

        # ----------------------------------------------------------------------
        # 5.4 Write each snippet to its own CSV, classify, and record result
        # ----------------------------------------------------------------------
        with classification_csv.open("a", encoding="utf-8", newline="") as cf:
            writer = csv.writer(cf)
            if cf.tell() == 0:                                     # Header only once
                writer.writerow(["type", "IDS"])

            for idx, snippet in enumerate(glass_examples):
                # Determine output filename (append index if multiple snippets)
                filename = (f"{table_file.stem}-{idx}.csv"
                            if len(glass_examples) > 1
                            else f"{table_file.stem}.csv")
                out_path = output_path / filename

                # Keep only lines that look like CSV rows (≥2 commas)
                cleaned_lines = "\n".join(
                    line for line in snippet.splitlines() if line.count(",") > 1
                )
                out_path.write_text(cleaned_lines, encoding="utf-8")

                # Detect basis for the snippet; override if JSON provided a stronger hint
                snippet_basis = basis_type(snippet)
                final_basis   = json_basis if snippet_basis == "none" and json_basis in ("molar", "massic") else snippet_basis
                overrides    += (final_basis != snippet_basis)

                # Record classification
                writer.writerow([final_basis, str(out_path)])

        print(f"[DEBUG] Overrides for {patent_dir.name}: {overrides}")
        print(f"Processed → {output_path}")

    except Exception as e:
        # Any parsing failure results in the file being moved for later analysis
        dest = not_splitted_path / table_file.name
        shutil.copy(table_file, dest)
        print(f"Error {table_file.name}: {e} → moved")

print("Operation completed successfully.")

# ------------------------------------------------------------------------------
# 6. Produce end-of-run statistics
# ------------------------------------------------------------------------------

counts = {"molar": 0, "massic": 0, "both": 0, "none": 0}
total  = 0
if classification_csv.exists():
    with classification_csv.open(encoding="utf-8") as cf:
        reader = csv.reader(cf)
        next(reader, None)                                         # Skip header
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
