import pandas as pd
import pickle


# Carregar os dois DataFrames a partir dos arquivos CSV (está local, REVEJA)
df1 = pd.read_csv("C:/Users/Eric_/OneDrive/Área de Trabalho/Ml-Vidros/vidros/final_filtered_concatenated-Copia.csv")
df2 = pd.read_csv("C:/Users/Eric_/OneDrive/Área de Trabalho/Ml-Vidros/vidros/refractiveIndex.csv")

# Função para verificar se a string contém apenas caracteres alfanuméricos e ASCII
def is_alphanumeric_ascii(s):
    return all(char.isalnum() and ord(char) < 128 for char in s)

print(df1)