import json
import re
import unicodedata
import csv
from pathlib import Path
import pandas as pd

def normalize_string(s: str) -> str:
    """
    Normalize a string by:
      - applying Unicode NFKD normalization
      - removing accents
      - stripping whitespace
      - converting to lowercase
    """
    s = str(s)
    nkfd = unicodedata.normalize("NFKD", s)
    no_accents = nkfd.encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"\s+", "", no_accents).lower()


def load_desired_compounds(json_path: Path) -> list[str]:
    """
    Load the list of desired compounds from the given JSON file,
    normalizing each entry.
    """
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [normalize_string(comp) for comp in data.get("desired_compounds", [])]


def make_signature(row: pd.Series, cols: list[str]) -> tuple:
    """
    Given a row and a list of columns, return a tuple of the values
    in those columns. Used to compare full compositions.
    """
    return tuple(row[col] for col in cols)


def compare_compositions(csv1_path: Path, csv2_path: Path, props_json: Path):
    # Load desired compounds
    desired = load_desired_compounds(props_json)

    # Read both CSVs
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

    # Normalize column names
    df1.columns = [normalize_string(c) for c in df1.columns]
    df2.columns = [normalize_string(c) for c in df2.columns]

    # Identify the IDS column
    key_col = "ids"
    if key_col not in df1.columns or key_col not in df2.columns:
        raise KeyError(f"'{key_col.upper()}' column not found in one of the CSVs.")

    # Find which desired compounds actually appear in both CSVs
    comp_cols = [c for c in desired if c in df1.columns and c in df2.columns]
    if not comp_cols:
        raise ValueError("No desired compound columns found in common between the two CSVs.")

    # Subset to IDS + desired compounds
    sub1 = df1[[key_col] + comp_cols].copy()
    sub2 = df2[[key_col] + comp_cols].copy()

    # Ensure numeric types for comparison
    for col in comp_cols:
        sub1[col] = pd.to_numeric(sub1[col], errors="coerce")
        sub2[col] = pd.to_numeric(sub2[col], errors="coerce")

    # Build a "signature" tuple for each row
    sub1["signature"] = sub1.apply(lambda r: make_signature(r, comp_cols), axis=1)
    sub2["signature"] = sub2.apply(lambda r: make_signature(r, comp_cols), axis=1)

    # Determine common and unique signatures
    sigs1 = set(sub1["signature"])
    sigs2 = set(sub2["signature"])
    common_sigs = sigs1 & sigs2

    common_rows = sub1[sub1["signature"].isin(common_sigs)].copy()
    unique1 = sub1[~sub1["signature"].isin(common_sigs)].copy()
    unique2 = sub2[~sub2["signature"].isin(common_sigs)].copy()

    # Write the comparison CSV
    out_path = csv1_path.parent / "compositions_compared.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Common compositions
        writer.writerow(["Common composition"])
        writer.writerow([key_col.upper()] + [c.upper() for c in comp_cols])
        for _, row in common_rows.sort_values(by=key_col).iterrows():
            writer.writerow([row[key_col]] + [row[c] for c in comp_cols])
        writer.writerow([])

        # Unique to first CSV
        writer.writerow([f"Unic compositions for {csv1_path.name}"])
        writer.writerow([key_col.upper()] + [c.upper() for c in comp_cols])
        for _, row in unique1.sort_values(by=key_col).iterrows():
            writer.writerow([row[key_col]] + [row[c] for c in comp_cols])
        writer.writerow([])

        # Unique to second CSV
        writer.writerow([f"Unic compositions for {csv2_path.name}"])
        writer.writerow([key_col.upper()] + [c.upper() for c in comp_cols])
        for _, row in unique2.sort_values(by=key_col).iterrows():
            writer.writerow([row[key_col]] + [row[c] for c in comp_cols])

    # Print summary statistics
    print(f"Rows in {csv1_path.name}: {len(sub1)}")
    print(f"Rows in {csv2_path.name}: {len(sub2)}")
    print(f"Common compositions: {len(common_rows)}")
    print(f"Unic compositions in {csv1_path.name}: {len(unique1)}")
    print(f"Unic compositions in {csv2_path.name}: {len(unique2)}")
    print(f"Arquivo '{out_path.name}' gerado com sucesso.")

if __name__ == "__main__":
    # Folder containing the two CSVs
    folder = Path(r"C:\Users\user\Documents\llm-glass-testes\data\filtered")
    # Hard-coded CSV filenames
    csv1 = folder / "csv_for_comparison_1.csv"
    csv2 = folder / "csv_for_comparison_2.csv"
    # Correct JSON folder and filename
    props_json = Path(r"C:\Users\user\Documents\llm-glass-testes\json") / "properties.json"

    compare_compositions(csv1, csv2, props_json)
