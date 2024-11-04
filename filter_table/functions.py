import json
import pandas as pd
from pathlib import Path  
import re
#teste
base_path = Path("data/raw")

csv_path1 = base_path / "final_filtered_concatenated.csv"
csv_path2 = base_path / "refractiveIndex.csv"
csv_path3 = base_path / "merged_df.csv"

dataframe1 = pd.read_csv(csv_path1)
dataframe2 = pd.read_csv(csv_path2)
dataframe3 = pd.read_csv(csv_path3)

json_path =  Path("json/properties.json")

with open(json_path, 'r') as file:
    data = json.load(file)

def Filter_By_Compounds(dataframe):
    lista=[]
    desired_compounds = data["desired_compounds"]
    for i in list(dataframe.columns):
        if i in desired_compounds:
            lista.append(i)
    return dataframe[lista]

def Filter_by_have_numbers(dataframe):
    columns_list_dataframe = list(dataframe.columns)
    lista=[]
    for i in columns_list_dataframe:
        a=re.findall(r'\d+', i)
        if a:
            lista.append(i)
    return dataframe[lista]

def Filter_by_2to8(dataframe):
    lista = []
    columns_list_dataframe = list(dataframe.columns)
    for i in columns_list_dataframe:
        if 2 <= len(i) <= 8:
            lista.append(i)
    return dataframe[lista]

def Pull_Apart_Compoundsdataframe_NotCompoundsdataframe(dataframe):
    dataframe_with_numbers=Filter_by_have_numbers(dataframe)
    dataframe_with_compounds=Filter_by_2to8(dataframe_with_numbers)
    dataframe_without_compounds=dataframe_with_compounds.columns.difference(dataframe.columns)
    return dataframe_with_compounds , dataframe_without_compounds

def Filter_by_not_plus(dataframe):
    lista=[]
    for i in dataframe.columns:
        if "+" not in i:
            lista.append(i)
    return dataframe[lista]

def insert_zeros(dataframe):
    # substituir '—' por 0
    dataframe = dataframe.replace('—', 0, inplace=True)
    # substituir NaN por 0
    dataframe = dataframe.fillna(0, inplace=True)
    # converte todas as colunas para numéricas
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

def sum_lines(dataframe, tolerance=2):
    # soma das linhas que contem os elementos desejados
    filtered_dataframe=Filter_By_Compounds(dataframe)
    columns=filtered_dataframe.columns
    soma_linhas = dataframe[columns].sum(axis=1)
    # linhas que somam 100
    linhas_que_somam_100 = dataframe[(soma_linhas >= 100 - tolerance) & (soma_linhas <= 100 + tolerance)]
    return linhas_que_somam_100

def filter_by_properties(dataframe):
    # lista de propriedades
    propriedades = ["refractive", "abbe", "liquidus", "c.", "density", "α", "modulus", "fiber", "devitrification",
                "point", "crystallization", "thermal", "mean", "glass transition", "crystallinity", "electric",
                "onset", "transition", "permittivity", "iso"]

    # colunas com alguma das propriedades
    properties_columns = [col for col in dataframe.columns if any(prop.lower() in col.lower() for prop in propriedades)]
    return dataframe[properties_columns]
    
def dataframe_sum_and_properties(dataframe):
    #dataframe com as linhas que somam 100 e as colunas de elementos desejados
    filtered_dataframe=Filter_By_Compounds(dataframe)
    linhas_que_somam_100=sum_lines(dataframe)
    properties_columns=filter_by_properties(dataframe).columns
    dataframe_filtered = filtered_dataframe.loc[linhas_que_somam_100.index]
    #soma das linhas das propriedades
    soma_linhas_propriedades = dataframe[properties_columns].sum(axis=1)
    nao_nulas = dataframe[soma_linhas_propriedades != 0]
    #adicionando as colunas de propriedades no final
    dataframe_final = pd.concat([dataframe_filtered, dataframe[properties_columns].loc[nao_nulas.index]], axis=1)
    return dataframe_final

    # a fazer: converter os elementos que não estãoe em % para %, juntar colunas iguais, dar uma olhada para ver se tem algo estranho
    # descobrir pq tem varias linhas NaN nas colunas de propriedades

teste=Filter_by_have_numbers(dataframe3)
teste=Filter_by_2to8(dataframe3)
teste=Pull_Apart_Compoundsdataframe_NotCompoundsdataframe(dataframe3)
print(teste)