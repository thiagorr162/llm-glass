import json
import re
import unicodedata
import csv
import shutil
from pathlib import Path
import pandas as pd

def normalize_string(s: str) -> str:
    """
    Normalize a string by:
      - applying Unicode NFKD
      - removing accents
      - removing whitespace
      - lower‑casing
    """
    s = str(s)
    nkfd = unicodedata.normalize("NFKD", s)
    no_accents = nkfd.encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"\s+", "", no_accents).lower()


def load_desired_compounds(json_path: Path) -> list[str]:
    """Read desired_compounds list and normalize each entry."""
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [normalize_string(c) for c in data.get("desired_compounds", [])]


def make_signature(row: pd.Series, cols: list[str]) -> tuple:
    """Return a tuple with the values of *cols* in *row* (full‑row signature)."""
    return tuple(row[col] for col in cols)

def compare_compositions(csv1_path: Path, csv2_path: Path, props_json: Path):
    desired = load_desired_compounds(props_json)

    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

    df1.columns = [normalize_string(c) for c in df1.columns]
    df2.columns = [normalize_string(c) for c in df2.columns]

    key_col = "ids"
    if key_col not in df1.columns or key_col not in df2.columns:
        raise KeyError("'IDS' column not found in one of the CSVs")

    comp_cols = [c for c in desired if c in df1.columns and c in df2.columns]
    if not comp_cols:
        raise ValueError("No desired_compound columns present in both CSVs")

    sub1 = df1[[key_col] + comp_cols].copy()
    sub2 = df2[[key_col] + comp_cols].copy()

    for col in comp_cols:
        sub1[col] = pd.to_numeric(sub1[col], errors="coerce")
        sub2[col] = pd.to_numeric(sub2[col], errors="coerce")

    sub1["signature"] = sub1.apply(lambda r: make_signature(r, comp_cols), axis=1)
    sub2["signature"] = sub2.apply(lambda r: make_signature(r, comp_cols), axis=1)

    common_sigs = set(sub1["signature"]) & set(sub2["signature"])
    common_rows = sub1[sub1["signature"].isin(common_sigs)]
    unique1 = sub1[~sub1["signature"].isin(common_sigs)].copy()
    unique2 = sub2[~sub2["signature"].isin(common_sigs)].copy()

    # ---------- CSV with overall comparison ---------- #
    out_path = csv1_path.parent / "compositions_compared.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Common composition"])
        w.writerow([key_col.upper()] + [c.upper() for c in comp_cols])
        for _, r in common_rows.sort_values(by=key_col).iterrows():
            w.writerow([r[key_col]] + [r[c] for c in comp_cols])
        w.writerow([])
        w.writerow([f"Unique compositions for {csv1_path.name}"])
        w.writerow([key_col.upper()] + [c.upper() for c in comp_cols])
        for _, r in unique1.sort_values(by=key_col).iterrows():
            w.writerow([r[key_col]] + [r[c] for c in comp_cols])
        w.writerow([])
        w.writerow([f"Unique compositions for {csv2_path.name}"])
        w.writerow([key_col.upper()] + [c.upper() for c in comp_cols])
        for _, r in unique2.sort_values(by=key_col).iterrows():
            w.writerow([r[key_col]] + [r[c] for c in comp_cols])

    print(f"Rows in {csv1_path.name}: {len(sub1)}")
    print(f"Rows in {csv2_path.name}: {len(sub2)}")
    print(f"Common compositions: {len(common_rows)}")
    print(f"Unique compositions in {csv1_path.name}: {len(unique1)}")
    print(f"Unique compositions in {csv2_path.name}: {len(unique2)}")
    print(f"File '{out_path.name}' generated successfully.")

    #Check ‘at least N’ #
    thresholds = [3, 4, 5]             # ← ao menos 3, 4, 5 valores iguais
    counts         = {n: 0 for n in thresholds}
    matching_pairs = {n: [] for n in thresholds}

    arr1 = unique1[comp_cols].to_numpy()
    arr2 = unique2[comp_cols].to_numpy()

    # For every row in unique1, test each threshold independently,
    # searching until find the first pair that satisfies ≥N;
    # then go to the nex threshold in the same row
    for i, row_vals in enumerate(arr1):
        for n in thresholds:
            for j, other_vals in enumerate(arr2):
                matches = int(((row_vals == other_vals) & (row_vals != 0)).sum())
                if matches >= n:
                    counts[n] += 1
                    matching_pairs[n].append((unique1.iloc[i], unique2.iloc[j]))
                    break  # stop scanning other rows for this (row1, n)
            # continue with next threshold for this same row1

    total_unique1 = len(unique1)
    for n in thresholds:
        print(f"Of the {total_unique1} unique rows in {csv1_path.name}, "
              f"{counts[n]} have at least {n} identical non‑zero values "
              f"in unique rows of {csv2_path.name}")
    print("Vice versa comparison would yield the same counts by symmetry.")

    analysis_dir = csv1_path.parent / "row_analysis"
    if analysis_dir.exists():
        shutil.rmtree(analysis_dir)
    analysis_dir.mkdir()

    # possible_equal_rows.csv
    pe_rows = []
    for n in thresholds:
        for r1, r2 in matching_pairs[n]:
            rec1 = {"THRESHOLD": n, "ORIGINAL_CSV": 1, key_col.upper(): r1[key_col]}
            rec2 = {"THRESHOLD": n, "ORIGINAL_CSV": 2, key_col.upper(): r2[key_col]}
            for c in comp_cols:
                rec1[c.upper()] = r1[c]
                rec2[c.upper()] = r2[c]
            pe_rows.extend([rec1, rec2])

    pd.DataFrame(pe_rows).to_csv(analysis_dir / "possible_equal_rows.csv", index=False)

    #Copy table files referenced by IDS 
    project_root = csv1_path.parent.parent.parent   # llm‑glass‑testes
    for id_val in set(r[key_col.upper()] for r in pe_rows):
        src = project_root / id_val
        if not src.exists():
            src = project_root / "data" / id_val
        if src.exists():
            shutil.copy2(src, analysis_dir / src.name)

    print(f"Row analysis artifacts written to '{analysis_dir}'")

#Runner
if __name__ == "__main__":
    folder     = Path(r"C:\Users\user\Documents\llm-glass-testes\data\filtered")
    csv1       = folder / "PROCESS_RECENTE_compounds_and_refractive(1414x76).csv"
    csv2       = folder / "PROCESS_RIGHT_compounds_and_refractive(1550x73).csv"
    props_json = Path(r"C:\Users\user\Documents\llm-glass-testes\json") / "properties.json"
    compare_compositions(csv1, csv2, props_json)
