import pathlib
import re
import unicodedata
import pandas as pd
import csv

# ignora esse codigo, só estou usando pra testar o process 
# Função para normalizar strings: remove espaços, acentos e converte para letras minúsculas
def normalize_string(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKD", s)
                  .encode("ASCII", "ignore").decode("utf-8").lower())

# Função para verificar se um valor é numérico
def is_numeric(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

# Dados de teste
rows = [
    ['White pigment', 'Index of refraction', 'Density (g/cm3)', '-', '-'],
    ['Rutile TiO2', '2.73', '4.3', '-', '-', '-', '-'],
    ['Detitanium-ore-type TiO2', '2.55', '3.9', '-', '-', '-', '-'],
    ['Zinc oxide', '2.02', '5.6', '-', '-', '-', '-'],
    ['White lead', '1.94-2.09', '5.5', '-', '-'],
    ['Lithopone', '1.84', '4.3', '-', '-', '-', '-'],
    ['Barite', '1.64', '4.5', '-', '-', '-', '-'],
    ['Calcium carbonate', '1.63', '2.8', '-', '-', '-', '-']
]

# Processa cada linha para identificar o primeiro valor numérico e gaps antes dele
rows_info = []
max_left_gap = 0

for row in rows[1:]:
    shift_left_count = 0
    first_numeric_idx = None
    for idx, cell in enumerate(row):
        cell_strip = cell.strip()
        if cell_strip in ['', '-', ' ']:
            shift_left_count += 1
        elif is_numeric(cell_strip):
            first_numeric_idx = idx
            break
        else:
            continue
    if first_numeric_idx is None:
        first_numeric_idx = len(row)
    if shift_left_count > max_left_gap:
        max_left_gap = shift_left_count
    rows_info.append({
        'row': row,
        'first_numeric_idx': first_numeric_idx,
        'shift_left_count': shift_left_count
    })

# Ajuste à esquerda (shift)
adjusted_rows = []
for info in rows_info:
    row = info['row']
    f_idx = info['first_numeric_idx']
    left_count = info['shift_left_count']
    if left_count < max_left_gap:
        diff = max_left_gap - left_count
        row = row[:f_idx] + ['-'] * diff + row[f_idx:]
    adjusted_rows.append(row)

# Completa linhas curtas com '-'
max_total_columns = max(len(r) for r in adjusted_rows)
final_rows = []
for r in adjusted_rows:
    if len(r) < max_total_columns:
        r = r + ['-'] * (max_total_columns - len(r))
    final_rows.append(r)

# Transforma em DataFrame e transpõe
df = pd.DataFrame(final_rows).dropna(axis=1, how="all").T

# Salva o resultado em data/filtered/testando.csv
output_path = pathlib.Path("data/filtered")
output_path.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path / "testando.csv", index=False, header=False)
print("Arquivo salvo em:", output_path / "testando.csv")
