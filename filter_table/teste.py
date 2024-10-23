import pandas as pd
from pathlib import Path
base_path = Path.home() / "Documents" / "VSCODE"
csv_path1 = base_path / "filtro" / "final_filtered_concatenated-Copia.csv"
csv_path2 = base_path / "ml_vidros-main" / "data" / "raw" / "refractiveIndex.csv"

df1 = pd.read_csv(csv_path1)
df2 = pd.read_csv(csv_path2)

columns_list_sketch = list(df2.columns)

desired_compounds = ["SiO2","P2O5","ZrO2","Na2O","Al2O3","Fe2O3","CaO","MgO","K2O","B2O3","MnO","BaO","ZnO","GeO2","Li2O","Ta2O5","SrO","CdO","SnO2","La2O3","Ga2O3","Y2O3","TiO2","Nb2O5","PbO","HfO2","WO3","Sb2O3","Bi2O3","Cr2O3","Cu2O","BeO","CuO","Nd2O3","CeO2","Cs2O","As2O3","Rb2O","Eu2O3","MoO3","FeO","Mn2O3","ThO2","Ag2O","MnO2","TeO2","Tl2O","CoO","In2O3","Sc2O3","NiO","V2O5","As2O5","Sm2O3","Gd2O3","Tb2O3","Dy2O3","Er2O3","Yb2O3","SnO","Ce2O3","Pr2O3","VO6","Pr6O11","Ni2O3","V2O3","Lu2O3","HgO","Tm2O3","Nb2O3","Tl2O3","Ta2O3","Tb4O7"]
filtered_columns=[]
for i in columns_list_sketch:
    if i in desired_compounds:
        filtered_columns.append(i)


filtered_dataframe2=df2[filtered_columns]

columns_list_df1 = list(df1.columns)
filter_by_not_plus=[]
for i in columns_list_df1:
    if "+" not in i:
        filter_by_not_plus.append(i)

lowercase_desired_compounds = [s.lower() for s in desired_compounds]
desired_glasses_df1=[]
for i in filter_by_not_plus:
    if i in lowercase_desired_compounds:
       desired_glasses_df1.append(i)
filtered_dataframe1=df1[desired_glasses_df1]
print(filtered_dataframe1)

# Dicionários para armazenar os resultados
numerical_values = {}
percent_values = {}
other_values = {}

# Separar linhas em três categorias para cada coluna de Colunas1
for coluna in filtered_columns:
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
