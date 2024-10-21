import pandas as pd
import pickle


# Carregar os dois DataFrames a partir dos arquivos CSV (está local, REVEJA)
df1 = pd.read_csv("C:/Users/Eric_/OneDrive/Área de Trabalho/Ml-Vidros/vidros/final_filtered_concatenated-Copia.csv")
df2 = pd.read_csv("C:/Users/Eric_/OneDrive/Área de Trabalho/Ml-Vidros/vidros/refractiveIndex.csv")

df2.rename(columns={'Unnamed: 0': 'names'}, inplace=True)

columns_list_sketch = list(df2.columns)

desired_compounds = ["SiO2","P2O5","ZrO2","Na2O","Al2O3","Fe2O3","CaO","MgO","K2O","B2O3","MnO","BaO","ZnO","GeO2","Li2O","Ta2O5","SrO","CdO","SnO2","La2O3","Ga2O3","Y2O3","TiO2","Nb2O5","PbO","HfO2","WO3","Sb2O3","Bi2O3","Cr2O3","Cu2O","BeO","CuO","Nd2O3","CeO2","Cs2O","As2O3","Rb2O","Eu2O3","MoO3","FeO","Mn2O3","ThO2","Ag2O","MnO2","TeO2","Tl2O","CoO","In2O3","Sc2O3","NiO","V2O5","As2O5","Sm2O3","Gd2O3","Tb2O3","Dy2O3","Er2O3","Yb2O3","SnO","Ce2O3","Pr2O3","VO6","Pr6O11","Ni2O3","V2O3","Lu2O3","HgO","Tm2O3","Nb2O3","Tl2O3","Ta2O3","Tb4O7"]
filtered_columns=[]
for i in columns_list_sketch:
    if i in desired_compounds:
        filtered_columns.append(i)


filtered_dataframe1=df2[filtered_columns]
print(filtered_dataframe1)