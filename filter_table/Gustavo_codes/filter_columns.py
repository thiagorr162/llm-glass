import pandas as pd
import pickle

# Função para verificar se a string contém apenas caracteres alfanuméricos e ASCII
def is_alphanumeric_ascii(s):
    return all(char.isalnum() and ord(char) < 128 for char in s)

# Carregar os dois DataFrames a partir dos arquivos CSV (está local, REVEJA)
df1 = pd.read_csv("C:\Users\Eric_\OneDrive\Área de Trabalho\Ml-Vidros\vidros\final_filtered_concatenated-Copia.csv")
df2 = pd.read_csv("C:\Users\Eric_\OneDrive\Área de Trabalho\Ml-Vidros\vidros\refractiveIndex.csv")

# Obter listas de colunas, convertendo para minúsculas para ignorar diferença de case
colunas_df1 = set(coluna.lower() for coluna in df1.columns)
colunas_df2 = set(coluna.lower() for coluna in df2.columns)

# Identificar colunas comuns
colunas_comuns = colunas_df1.intersection(colunas_df2)

# Filtrar colunas: 2-5 caracteres, ao menos um dígito, e apenas alfanuméricos ASCII
colunas_teste1 = [
    coluna for coluna in colunas_df1  # Aqui deve ser colunas_df1
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
with open("Colunas1.pkl", "wb") as f:
    pickle.dump(Colunas1, f)

print("\nLista de colunas coincidentes salva como 'Colunas1.pkl'.")