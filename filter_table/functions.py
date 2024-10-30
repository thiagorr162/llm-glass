import json
import pandas as pd
from pathlib import Path  
import re

base_path = Path("data/raw")

csv_path1 = base_path / "final_filtered_concatenated.csv"
csv_path2 = base_path / "refractiveIndex.csv"

dataframe1 = pd.read_csv(csv_path1)
dataframe2 = pd.read_csv(csv_path2)

json_path =  Path("json/properties.json")

with open(json_path, 'r') as file:
    data = json.load(file)

def Filter_By_Compounds(dataframe):
    list=[]
    desired_compounds = data["desired_compounds"]
    for i in list(dataframe.columns):
        if i in desired_compounds:
            list.append(i)
    return dataframe[list]

def Filter_by_have_numbers(dataframe):
    columns_list_dataframe = list(dataframe.columns)
    list=[]
    for i in columns_list_dataframe:
        a=re.findall(r'\d+', i)
        if a:
            list.append(i)
    return dataframe[list]

def Filter_by_2to8(dataframe):
    list = []
    columns_list_dataframe = list(dataframe.columns)
    for i in columns_list_dataframe:
        if 2 <= len(i) <= 8:
            list.append(i)
    return dataframe[list]

def Pull_Apart_Compoundsdataframe_NotCompoundsdataframe(dataframe):
    dataframe_with_numbers=dataframe[Filter_by_have_numbers(dataframe)]
    dataframe_with_compounds=dataframe_with_numbers[Filter_by_have_2to8(dataframe)]
    dataframe_without_compounds=dataframe[dataframe_with_compounds.columns.difference(dataframe1.columns)]
    return dataframe_with_compounds and dataframe_without_compounds

def Filter_by_not_plus(dataframe):
    list=[]
    for i in dataframe.columns:
        if "+" not in i:
            list.append(i)
    return dataframe[list]

#extra_fixes1=dataframe1['yo1.5']
#extra_fixes2=dataframe1['α1']
#filtered_dataframe1['yo1.5']=extra_fixes1
#filtered_dataframe1['α1']=extra_fixes2
#print(filtered_dataframe1)

def insert_zeros(dataframe):
    # substituir '—' por 0
    dataframe.replace('—', 0, inplace=True)
    # substituir NaN por 0
    dataframe.fillna(0, inplace=True)
    # converte todas as colunas para numéricas
    dataframe = dataframe.apply(pd.to_numeric, errors='coerce').fillna(0)
    return dataframe

def sum_lines(dataframe):
    # soma das linhas que contem os elementos desejados
    filtered_dataframe=Filter_By_Compounds(dataframe)
    columns=filtered_dataframe.columns
    soma_linhas = dataframe[columns].sum(axis=1)
    # linhas que somam 100
    linhas_que_somam_100 = dataframe[soma_linhas == 100]
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

    # soma das linhas das propriedades
    soma_linhas_propriedades = dataframe[properties_columns].sum(axis=1)
    nao_nulas = dataframe[soma_linhas_propriedades != 0]

    # adicionando as colunas de propriedades no final
    dataframe_final = pd.concat([dataframe_filtered, dataframe[properties_columns].loc[nao_nulas.index]], axis=1)
    return dataframe_final.to_csv(novo, index=False)

# a fazer: converter os elementos que não estãoe em % para %, juntar colunas iguais, dar uma olhada para ver se tem algo estranho
# descobrir pq tem varias linhas NaN nas colunas de propriedades