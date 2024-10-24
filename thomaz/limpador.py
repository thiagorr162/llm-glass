import pandas as pd
from pathlib import Path as path

# caminhos
raw = path("C:/Users/thoma/Downloads/final_filtered_concatenated.csv")
novo = path("C:/Users/thoma/Downloads/dataframe_teste.csv")

# le o dataframe
df = pd.read_csv(raw)

# substituir '—' por 0
df.replace('—', 0, inplace=True)
# substituir NaN por 0
df.fillna(0, inplace=True)

# converte todas as colunas para numéricas
df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

# elementos desejados
desired_compounds = ['sio2', 'p2o5', 'zro2', 'na2o', 'al2o3', 'fe2o3', 'cao', 'mgo', 'k2o', 'b2o3', 
                     'mno', 'bao', 'zno', 'geo2', 'li2o', 'ta2o5', 'sro', 'cdo', 'sno2', 'la2o3', 
                     'ga2o3', 'y2o3', 'tio2', 'nb2o5', 'pbo', 'hfo2', 'wo3', 'sb2o3', 'bi2o3', 
                     'cr2o3', 'cu2o', 'beo', 'cuo', 'nd2o3', 'ceo2', 'cs2o', 'as2o3', 'rb2o', 
                     'eu2o3', 'moo3', 'feo', 'mn2o3', 'tho2', 'ag2o', 'mno2', 'teo2', 'tl2o', 
                     'coo', 'in2o3', 'sc2o3', 'nio', 'v2o5', 'as2o5', 'sm2o3', 'gd2o3', 'tb2o3', 
                     'dy2o3', 'er2o3', 'yb2o3', 'sno', 'ce2o3', 'pr2o3', 'vo6', 'pr6o11', 
                     'ni2o3', 'v2o3', 'lu2o3', 'hgo', 'tm2o3', 'nb2o3', 'tl2o3', 'ta2o3', 'tb4o7']

# colunas com os elementos desejados
matching_columns = [col for col in df.columns if any(comp.lower() in col.lower() for comp in desired_compounds)]

# soma das linhas que contem os elementos desejados
soma_linhas = df[matching_columns].sum(axis=1)

# linhas que somam 100
linhas_que_somam_100 = df[soma_linhas == 100]

# lista de propriedades
propriedades = ["refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", "devitrification",
                "point", "crystallization", "thermal", "mean", "glass transition", "crystallinity", "electric",
                "onset", "transition", "permittivity", "iso"]

# colunas com alguma das propriedades
properties_columns = [col for col in df.columns if any(prop.lower() in col.lower() for prop in propriedades)]

# dataframe com as linhas que somam 100 e as colunas de elementos desejados
df_filtered = df[matching_columns].loc[linhas_que_somam_100.index]

# soma das linhas das propriedades
soma_linhas_propriedades = df[properties_columns].sum(axis=1)
nao_nulas = df[soma_linhas_propriedades != 0]

# adicionando as colunas de propriedades no final
df_final = pd.concat([df_filtered, df[properties_columns].loc[nao_nulas.index]], axis=1)

# arquivo novo
df_final.to_csv(novo, index=False)

print(df_final.head())
print(df_final.shape)

# a fazer: converter os elementos que não estãoe em % para %, juntar colunas iguais, dar uma olhada para ver se tem algo estranho
# descobrir pq tem varias linhas NaN nas colunas de propriedades