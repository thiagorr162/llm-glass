from pathlib import Path
import json
import re
import unicodedata
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# 1. Helper utilities
# --------------------------------------------------------------------------- #

def normalize_string(s: str) -> str:
    """
    Canonicalise a string for reliable column matching:
    - NFKD Unicode normalisation
    - accent strip
    - whitespace removal
    - lower-casing
    """
    nkfd = unicodedata.normalize("NFKD", str(s))
    return re.sub(r"\s+", "", nkfd.encode("ASCII", "ignore").decode("utf-8")).lower()


def load_desired_compounds(json_path: Path) -> list[str]:
    """Load the 'desired_compounds' list from *properties.json* (normalised)."""
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [normalize_string(c) for c in data.get("desired_compounds", [])]


def count_distinct_differences(a: np.ndarray, b: np.ndarray) -> int:
    """
    Return the number of oxides whose values disagree *and* where at least
    one of the two rows is non-zero.

    This counts both:
        • positions where a!=b and both are non-zero;
        • positions where one is non-zero and the other is zero.
    """
    mask = (a != b) & ((a != 0) | (b != 0))
    return int(np.count_nonzero(mask))


def is_potential_match_dynamic(a: np.ndarray, b: np.ndarray) -> bool:
    """
    Heuristic filter for near-duplicate rows.

    A pair qualifies when it differs in
        ≤1 oxide  (if the row is “sparse”, ≤7 non-zeros)  or
        ≤2 oxides (if the row is “dense”,  >7 non-zeros).
    """
    allowed = 2 if np.count_nonzero(a) > 7 else 1
    return count_distinct_differences(a, b) <= allowed


def select_one_closest_to_100(a: np.ndarray, b: np.ndarray) -> int:
    """
    Decide which row is closer to a 100 % oxide sum.

    Returns
    -------
    1  : keep *a*
    2  : keep *b*
    0  : exact tie (ignored)
    -1 : not a potential match
    """
    if not is_potential_match_dynamic(a, b):
        return -1
    d1, d2 = abs(a.sum() - 100.0), abs(b.sum() - 100.0)
    return 1 if d1 < d2 else (2 if d2 < d1 else 0)

# --------------------------------------------------------------------------- #
# 2. Core routine
# --------------------------------------------------------------------------- #

def compare_compositions(csv1_path: Path, csv2_path: Path, props_json: Path) -> None:
    # 1. Read CSVs and label provenance ------------------------------------ #
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)
    df1['_src'], df2['_src'] = 1, 2                 # 1 = LEFT, 2 = RIGHT
    df1['_row_num'], df2['_row_num'] = df1.index, df2.index

    # 2. Canonicalise headers, drop duplicates ----------------------------- #
    df1.columns = [normalize_string(c) for c in df1.columns]
    df2.columns = [normalize_string(c) for c in df2.columns]
    df1 = df1.loc[:, ~df1.columns.duplicated()]
    df2 = df2.loc[:, ~df2.columns.duplicated()]

    if 'ids' not in df1.columns or 'ids' not in df2.columns:
        raise KeyError("Both CSVs must contain an 'ids' column")

    # 3. Determine shared oxide columns ------------------------------------ #
    desired_norm = load_desired_compounds(props_json)
    comp_cols = [c for c in desired_norm if c in df1.columns and c in df2.columns]
    if not comp_cols:
        raise ValueError("No shared desired compounds were found")

    # 4. Build reduced working tables (ids + oxides) ----------------------- #
    sub1 = df1[['ids'] + comp_cols + ['_src', '_row_num']].copy()
    sub2 = df2[['ids'] + comp_cols + ['_src', '_row_num']].copy()

    # 5. Coerce oxide columns to numeric ----------------------------------- #
    for c in comp_cols:
        sub1[c] = pd.to_numeric(sub1[c], errors='coerce')
        sub2[c] = pd.to_numeric(sub2[c], errors='coerce')

    # 6. Exact signature matches ------------------------------------------- #
    sig1 = sub1[comp_cols].apply(tuple, axis=1)
    sig2 = sub2[comp_cols].apply(tuple, axis=1)
    common_sigs = set(sig1) & set(sig2)

    common  = sub1[sig1.isin(common_sigs)].reset_index(drop=True)
    unique1 = sub1[~sig1.isin(common_sigs)].reset_index(drop=True)
    unique2 = sub2[~sig2.isin(common_sigs)].reset_index(drop=True)
    print(f"Common: {len(common)}, Unique1: {len(unique1)}, Unique2: {len(unique2)}")

   # 7. One-to-one dynamic matching (near duplicates) ------------------------- #
    arr1, arr2 = unique1[comp_cols].to_numpy(), unique2[comp_cols].to_numpy()

    used_i: set[int] = set()          # rows of unique1 that already formed a pair
    used_j: set[int] = set()          # rows of unique2 that already formed a pair 

    winners1, losers1 = set(), set()
    winners2, losers2 = set(), set()
    pair_tuples: list[tuple[int, int, int]] = []   # (row_win, row_lose, src_win)

    for i in range(len(arr1)):
        if i in used_i:
            continue
        for j in range(len(arr2)):
            if j in used_j:           # ← ❶  **unique2 can pair only once**
                continue

            a, b = arr1[i], arr2[j]
            if not is_potential_match_dynamic(a, b):
                continue

            diff1, diff2 = abs(a.sum() - 100.0), abs(b.sum() - 100.0)

            if diff1 < diff2:                              # LEFT wins
                winners1.add(unique1.at[i, '_row_num'])
                losers2.add(unique2.at[j, '_row_num'])
                pair_tuples.append(
                    (unique1.at[i, '_row_num'],
                     unique2.at[j, '_row_num'], 1)
                )
            elif diff2 < diff1:                           # RIGHT wins
                winners2.add(unique2.at[j, '_row_num'])
                losers1.add(unique1.at[i, '_row_num'])
                pair_tuples.append(
                    (unique2.at[j, '_row_num'],
                     unique1.at[i, '_row_num'], 2)
                )
            else:                                         # exact tie → skip
                continue

            used_i.add(i)
            used_j.add(j)   # ← ❷  mark this row of unique2 as paired
            break           # only one j per i (and now only one i per j)

    print(f"W1={len(winners1)}, L1={len(losers1)}, "
          f"W2={len(winners2)}, L2={len(losers2)}")

    # Build DataFrame with dynamic winners
    dyn_records = []
    for idx in sorted(winners1):
        rec = unique1.loc[unique1['_row_num'] == idx].iloc[0]
        dyn_records.append({'_src': rec['_src'], '_row_num': idx,
                            **{c: rec[c] for c in comp_cols},
                            'SUM': float(rec[comp_cols].sum())})
    for idx in sorted(winners2):
        rec = unique2.loc[unique2['_row_num'] == idx].iloc[0]
        dyn_records.append({'_src': rec['_src'], '_row_num': idx,
                            **{c: rec[c] for c in comp_cols},
                            'SUM': float(rec[comp_cols].sum())})
    dyn_df = pd.DataFrame(dyn_records).reset_index(drop=True)

         # ——— DEBUG for rows_sum criteria ———
    analysis_dir = csv1_path.parent / "analysis"
    analysis_dir.mkdir(exist_ok=True)

    def build_debug_row(rec, role, pair_id, src_label):
        """
        Make the dict with:
          – PAIR_ID : Winner's IDS
          – ROLE    : 'WIN' ou 'LOSE'
          – SRC     : 1 (LEFT) ou 2 (RIGHT)
          – IDS, SUM, DIFF_SUM, values for each Desired Compound
        """
        return {
            "PAIR_ID":  pair_id,
            "ROLE":     role,
            "SRC":      src_label,
            "IDS":      rec["ids"],
            "SUM":      float(rec[comp_cols].sum()),
            "DIFF_SUM": abs(rec[comp_cols].sum() - 100.0),
            **{c.upper(): rec[c] for c in comp_cols}
        }

    pair_rows = []                                       

    for win_idx, lose_idx, src_w in pair_tuples:
        win_df  = unique1 if src_w == 1 else unique2
        lose_df = unique2 if src_w == 1 else unique1

        w = win_df .loc[win_df ['_row_num'] == win_idx ].iloc[0]
        l = lose_df.loc[lose_df['_row_num'] == lose_idx].iloc[0]

        diff_cols = [c.upper() for c in comp_cols
                     if w[c] != l[c] ]

        # Winner row
        pair_rows.append({
            **build_debug_row(w, "WIN",  win_idx, src_w),
            "DIFF_COLS": ";".join(diff_cols)
        })
        # Loser row
        pair_rows.append({
            **build_debug_row(l, "LOSE", win_idx, 3 - src_w),   # 3-src 1↔2
            "DIFF_COLS": ";".join(diff_cols)
        })

    debug_pairs = pd.DataFrame(pair_rows)
    debug_pairs.to_csv(analysis_dir / "dynamic_pairs_full.csv", index=False)
    print("Wrote dynamic-pairs debug CSV →", analysis_dir / "dynamic_pairs_full.csv")


    # 8. Assemble final DataFrame ------------------------------------------ #
    all_cols = sorted((set(df1.columns) | set(df2.columns)) - {'_src', '_row_num'})

    def fetch_rows(src: int, rows: list[int]) -> pd.DataFrame:
        """
        Retrieve original rows and reindex to *all_cols*,
        zero-filling any missing property/oxide columns.
        """
        df = df1 if src == 1 else df2
        return df.iloc[rows].reindex(columns=all_cols, fill_value=0).reset_index(drop=True)

    common_rows = common['_row_num'].tolist()
    u1_rows = [r for r in unique1['_row_num'] if r not in winners1 and r not in losers1]
    u2_rows = [r for r in unique2['_row_num'] if r not in winners2 and r not in losers2]

   # Construct each block and respective origin (_src)
    block_common = fetch_rows(1, common_rows)
    block_common['Origin'] = 'common'

    block_u1 = fetch_rows(1, u1_rows)
    block_u1['Origin'] = 'u1'

    block_u2 = fetch_rows(2, u2_rows)
    block_u2['Origin'] = 'u2'

   # Winners 1 and 2 remount, so _search exists
    blk1 = fetch_rows(1, sorted(winners1))
    blk1['_src'] = 1
    blk2 = fetch_rows(2, sorted(winners2))
    blk2['_src'] = 2
    block_dyn = pd.concat([blk1, blk2], ignore_index=True)
   # Map src=1 → dyn1, src=2 → dyn2
    block_dyn['Origin'] = block_dyn['_src'].map({1: 'dyn1', 2: 'dyn2'})

   #Count dyn 1 and dyn2
    counts = block_dyn['Origin'].value_counts()

    final_df = pd.concat([block_common, block_u1, block_u2, block_dyn],
                         ignore_index=True)
    print("Final block sizes:", {
        'common': len(block_common),
        'u1':     len(block_u1),
        'u2':     len(block_u2),
        'dyn1':   counts.get('dyn1',0),
        'dyn2':   counts.get('dyn2',0),
        'total':  len(final_df)
    })

    # 9. Restore oxide order, append extra properties, rename IDS ---------- #
    with props_json.open(encoding='utf-8') as jf:
        oxide_order = json.load(jf)["desired_compounds"]  # uppercase order

    norm_oxides = [normalize_string(o) for o in oxide_order]

    compounds_only = (final_df
                      .reindex(columns=norm_oxides, fill_value=0)
                      .rename(columns=dict(zip(norm_oxides, oxide_order))))

    prop_cols = [c for c in final_df.columns
                 if c not in norm_oxides and c != 'ids']
    properties_only = final_df[prop_cols]

    final_df = final_df.rename(columns={'ids': 'IDS'})
    post_processed = pd.concat([compounds_only, properties_only], axis=1)
    post_processed['IDS'] = final_df['IDS']

    # 10. Export ----------------------------------------------------------- #
    out_path = csv1_path.parent / "compounds_and_refractive_post_processed.csv"
    post_processed.to_csv(out_path, index=False)
    print("Wrote final filtered CSV →", out_path)

# --------------------------------------------------------------------------- #
# 3. CLI / runner
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    base = root / "data" / "filtered"

    # Locate LEFT and RIGHT CSVs
    left_files  = sorted(base.glob("LEFT_compounds_and_refractive*.csv"))
    right_files = sorted(base.glob("RIGHT_compounds_and_refractive*.csv"))
    if not left_files or not right_files:
        raise FileNotFoundError("LEFT or RIGHT input CSV not found")

    properties_file = root / "json" / "properties.json"

    compare_compositions(left_files[0], right_files[0], properties_file)
