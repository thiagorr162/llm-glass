import json
import re
import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

# ------------------ helpers ------------------ #

def normalize_string(s: str) -> str:
    """
    Normalize a string by:
      - applying Unicode NFKD
      - removing accents
      - removing whitespace
      - lower-casing
    """
    nkfd = unicodedata.normalize("NFKD", str(s))
    return re.sub(r"\s+", "", nkfd.encode("ASCII", "ignore").decode("utf-8")).lower()

def load_desired_compounds(json_path: Path) -> list[str]:
    """Read and normalize the desired_compounds list from JSON."""
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [normalize_string(c) for c in data.get("desired_compounds", [])]

def count_distinct_differences(a: np.ndarray, b: np.ndarray) -> int:
    mask = (a != 0) & (b != 0)
    return int(np.sum(a[mask] != b[mask]))

def is_potential_match_dynamic(a: np.ndarray, b: np.ndarray) -> bool:
    allowed = 2 if np.count_nonzero(a) > 7 else 1
    return count_distinct_differences(a, b) <= allowed

def select_one_closest_to_100(a: np.ndarray, b: np.ndarray) -> int:
    if not is_potential_match_dynamic(a, b):
        return -1
    d1, d2 = abs(a.sum() - 100.0), abs(b.sum() - 100.0)
    return 1 if d1 < d2 else (2 if d2 < d1 else 0)

# --------------- main routine ---------------- #

def compare_compositions(csv1_path: Path, csv2_path: Path, props_json: Path):
    # 1) Read & tag source and row index
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)
    df1['_src'], df2['_src'] = 1, 2
    df1['_row_num'], df2['_row_num'] = df1.index, df2.index

    # 2) Normalize & drop duplicate columns
    df1.columns = [normalize_string(c) for c in df1.columns]
    df2.columns = [normalize_string(c) for c in df2.columns]
    df1 = df1.loc[:, ~df1.columns.duplicated()]
    df2 = df2.loc[:, ~df2.columns.duplicated()]

    key = 'ids'
    if key not in df1.columns or key not in df2.columns:
        raise KeyError(f"'{key}' column not found in one of the CSVs")

    # 3) Desired-compound intersection
    desired_norm = load_desired_compounds(props_json)
    comp_cols = [c for c in desired_norm if c in df1.columns and c in df2.columns]
    if not comp_cols:
        raise ValueError("No desired_compound columns present in both CSVs")

    # 4) Build sub-tables with tags
    sub1 = df1[[key] + comp_cols + ['_src', '_row_num']].copy()
    sub2 = df2[[key] + comp_cols + ['_src', '_row_num']].copy()

    # 5) Numeric conversion for matching
    for col in comp_cols:
        sub1[col] = pd.to_numeric(sub1[col], errors='coerce')
        sub2[col] = pd.to_numeric(sub2[col], errors='coerce')

    # 6) Exact signature matches
    sig1 = sub1[comp_cols].apply(tuple, axis=1)
    sig2 = sub2[comp_cols].apply(tuple, axis=1)
    common_sigs = set(sig1) & set(sig2)

    common  = sub1[sig1.isin(common_sigs)].reset_index(drop=True)
    unique1 = sub1[~sig1.isin(common_sigs)].reset_index(drop=True)
    unique2 = sub2[~sig2.isin(common_sigs)].reset_index(drop=True)

    print(f"Common: {len(common)}, Unique1: {len(unique1)}, Unique2: {len(unique2)}")

    # 7) Dynamic sum-to-100 picks
    arr1, arr2 = unique1[comp_cols].to_numpy(), unique2[comp_cols].to_numpy()
    chosen = []
    for i, a in enumerate(arr1):
        for j, b in enumerate(arr2):
            sel = select_one_closest_to_100(a, b)
            if sel in (1, 2):
                rec = unique1.iloc[i] if sel == 1 else unique2.iloc[j]
                chosen.append({
                    '_src': rec['_src'],
                    '_row_num': rec['_row_num'],
                    'SRC': sel,
                    **{c: rec[c] for c in comp_cols},
                    'SUM': float(rec[comp_cols].sum())
                })
                break

    dyn_df = (pd.DataFrame(chosen)
              .drop_duplicates(subset=['_src', '_row_num'])
              .reset_index(drop=True))
    print("Dynamic picks by source:", dyn_df['SRC'].value_counts().to_dict())

    # 8) Assemble final by original indices
    all_cols = sorted((set(df1.columns) | set(df2.columns)) - {'_src', '_row_num'})

    def fetch_rows(src: int, rows: list[int]) -> pd.DataFrame:
        df = df1 if src == 1 else df2
        sel = df.iloc[rows]
        return sel.reindex(columns=all_cols, fill_value=0).reset_index(drop=True)

    common_rows = common['_row_num'].tolist()
    dyn1_rows   = dyn_df.query('SRC == 1')['_row_num'].tolist()
    dyn2_rows   = dyn_df.query('SRC == 2')['_row_num'].tolist()
    u1_rows     = [r for r in unique1['_row_num'] if r not in dyn1_rows]
    u2_rows     = [r for r in unique2['_row_num'] if r not in dyn2_rows]

    block_common = fetch_rows(1, common_rows)
    block_u1     = fetch_rows(1, u1_rows)
    block_u2     = fetch_rows(2, u2_rows)
    block_dyn    = pd.concat([
                        fetch_rows(1, dyn1_rows),
                        fetch_rows(2, dyn2_rows)
                    ], ignore_index=True)

    final_df = pd.concat(
        [block_common, block_u1, block_u2, block_dyn],
        ignore_index=True
    )

    print("Final block sizes:", {
        'common': len(block_common),
        'u1':     len(block_u1),
        'u2':     len(block_u2),
        'dyn':    len(block_dyn),
        'total':  len(final_df)
    })

    # 9) Restore every desired oxide (uppercase, JSON order), then properties, then IDS
    with props_json.open('r', encoding='utf-8') as jf:
        data = json.load(jf)
    oxide_order = data["desired_compounds"]  # uppercase list from JSON
    norm_oxides  = [normalize_string(o) for o in oxide_order]

    # pick/zero-fill oxide cols and rename back to uppercase. ARRUMAR ISSO
    compounds_only = (
        final_df
        .reindex(columns=norm_oxides, fill_value=0)
        .rename(columns=dict(zip(norm_oxides, oxide_order)))
    )

    # property columns = anything else except 'ids'
    prop_cols = [c for c in final_df.columns if c not in norm_oxides and c != 'ids']
    properties_only = final_df[prop_cols]

    # rename 'ids' → 'IDS' and append at end
    final_df = final_df.rename(columns={'ids': 'IDS'})
    post_processed = pd.concat([compounds_only, properties_only], axis=1)
    post_processed['IDS'] = final_df['IDS']

    # 10) Export
    out_path = csv1_path.parent / "compounds_and_refractive_post_processed.csv"
    post_processed.to_csv(out_path, index=False)
    print("Wrote final filtered CSV →", out_path)

# ------------------ runner ------------------ #

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    base = root / "data" / "filtered"
    compare_compositions(
        base / "PROCESS_LEFT_compounds_and_refractive(1414x76).csv",
        base / "PROCESS_RIGHT_compounds_and_refractive(1550x73).csv",
        root / "json" / "properties.json"
    )
