#---------------importação

import pandas as pd
import pickle
from pathlib import Path

# Função para verificar se a string contém apenas caracteres alfanuméricos e ASCII
def is_alphanumeric_ascii(s):
    return all(char.isalnum() and ord(char) < 128 for char in s)

# Definir os caminhos dos arquivos usando Path
base_path = Path.home() / "Documents" / "VSCODE"
csv_path1 = base_path / "filtro" / "final_filtered_concatenated-Copia.csv"
csv_path2 = base_path / "ml_vidros-main" / "data" / "raw" / "refractiveIndex.csv"
pkl_path = Path("Colunas1.pkl")  # Salvar na pasta atual

# Carregar os DataFrames a partir dos arquivos CSV
df1 = pd.read_csv(csv_path1)
df2 = pd.read_csv(csv_path2)

# Obter listas de colunas, convertendo para minúsculas para ignorar diferenças de case
colunas_df1 = set(coluna.lower() for coluna in df1.columns)
colunas_df2 = set(coluna.lower() for coluna in df2.columns)

# Identificar colunas comuns
colunas_comuns = colunas_df1.intersection(colunas_df2)

# Filtrar colunas: 2-5 caracteres, ao menos um dígito, e apenas alfanuméricos ASCII
colunas_teste1 = [
    coluna for coluna in colunas_df1
    if 2 <= len(coluna) <= 5
    and any(char.isdigit() for char in coluna)
    and not coluna.isdigit()
    and is_alphanumeric_ascii(coluna)
]

# Comparar colunas comuns com colunas_teste1
coincidentes = colunas_comuns.intersection(colunas_teste1)
nao_coincidentes = set(colunas_teste1) - colunas_comuns

# Armazenar colunas coincidentes em uma lista
Colunas1 = list(coincidentes)

# Exibir resultados
print("Colunas Coincidentes:")
for idx, coluna in enumerate(Colunas1):
    print(f"{idx}: {coluna}")

print("\nColunas Não Coincidentes:")
for idx, coluna in enumerate(nao_coincidentes):
    print(f"{idx}: {coluna}")

# Salvar a lista de colunas coincidentes como um arquivo .pkl
with pkl_path.open("wb") as f:
    pickle.dump(Colunas1, f)

print(f"\nLista de colunas coincidentes salva como '{pkl_path.name}'.")

#-------------------visualização

# Dicionários para armazenar os resultados
numerical_values = {}
percent_values = {}
other_values = {}

# Separar linhas em três categorias para cada coluna de Colunas1
for coluna in Colunas1:
    # Linhas com valores numéricos (composições)
    numerical_values[coluna] = df1[coluna].dropna()[df1[coluna].apply(lambda x: isinstance(x, (int, float)))].tolist()

    # Linhas com "percent" ou "%" em qualquer parte do conteúdo (somente se for string)
    if df1[coluna].dtype == 'object':  # Verifica se a coluna contém strings
        percent_values[coluna] = tuple(df1[coluna][df1[coluna].str.contains(r"\bpercent\b|\%", case=False, na=False)].tolist())
    else:
        percent_values[coluna] = ()  # Se não for string, armazena tupla vazia

    # Linhas com NaN e valores restantes que não são "percent" ou "%"
    other_values[coluna] = df1[coluna][
        df1[coluna].isna() | ~df1[coluna].astype(str).str.contains(r"\bpercent\b|\%", case=False, na=False)
    ].tolist()

    # Tentar converter elementos de other_values para numéricos e mover para numerical_values
    converted_values = []
    remaining_values = []

    # Listagem de símbolos que serão convertidos para zero
    zero_like_symbols = {"", "-", "–", "—", "_", " "}

    for value in other_values[coluna]:
        # Substituir NaN e símbolos equivalentes por zero
        if pd.isna(value) or str(value).strip() in zero_like_symbols:
            converted_values.append(0.0)
        else:
            try:
                # Tenta converter para float
                numeric_value = float(value)
                converted_values.append(numeric_value)
            except (ValueError, TypeError):
                # Se falhar, mantém no other_values
                remaining_values.append(value)

    # Adiciona os valores convertidos ao numerical_values
    numerical_values[coluna].extend(converted_values)

    # Atualiza other_values com os valores que não puderam ser convertidos
    other_values[coluna] = remaining_values

# Exibir os resultados
print("Linhas preenchidas com números (composições) em cada coluna:")
for coluna, values in numerical_values.items():
    print(f"{coluna}: {values}")

print("\nLinhas preenchidas com 'percent' e '%' em cada coluna:")
for coluna, values in percent_values.items():
    print(f"{coluna}: {values}")

print("\nLinhas com NaN e valores restantes em cada coluna:")
for coluna, values in other_values.items():
    print(f"{coluna}: {values}")


    #----------------rearranjo, teste 1

    # Dicionário para armazenar as novas colunas
new_columns = {
    "weight percent": {},
    "mol %": {},
    "mol. %": {}
}

def extract_values_between_titles(percent_vals, num_vals):
    """
    Extrai valores entre títulos e associa à categoria apropriada.
    """
    current_category = None  # Categoria ativa
    categorized_data = {key: [] for key in new_columns}  # Inicializa armazenamento

    # Garantir que ambos sejam listas
    percent_vals = list(percent_vals)  # Converte tupla para lista, se necessário
    num_vals = list(num_vals)  # Garantir que os valores numéricos estejam em lista

    # Combina percentuais e valores numéricos em uma lista única e ordenada
    combined_values = percent_vals + num_vals

    # Itera pela lista de valores combinados
    for value in combined_values:
        value = str(value).strip().lower()  # Normaliza para evitar inconsistências

        if value in new_columns:
            # Se encontramos um título, atualizamos a categoria ativa
            current_category = value
            print(f"Categoria ativa: {current_category}")  # Debug
        elif current_category:
            try:
                # Tenta converter para float e adiciona à categoria ativa
                numeric_value = float(value)
                categorized_data[current_category].append(numeric_value)
                print(f"Adicionado {numeric_value} à categoria {current_category}")  # Debug
            except ValueError:
                # Se não for um valor numérico válido, ignora
                print(f"Valor ignorado: {value}")  # Debug

    return categorized_data

# Itera sobre cada coluna de Colunas1
for coluna in Colunas1:
    # Extrai os valores de percent_values e numerical_values
    percent_vals = percent_values.get(coluna, [])
    num_vals = numerical_values.get(coluna, [])

    # Organiza os valores nas categorias apropriadas
    categorized_values = extract_values_between_titles(percent_vals, num_vals)

    # Armazena os resultados em new_columns
    for category, values in categorized_values.items():
        new_columns[category][coluna] = values

# Exibe os resultados
for category, colunas in new_columns.items():
    print(f"\nValores da categoria '{category}':")
    for coluna, valores in colunas.items():
        print(f"{coluna}: {valores}")

print(Colunas1)