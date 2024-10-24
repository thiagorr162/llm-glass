import pandas as pd
from pathlib import Path

import re

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


columns_list_df1 = list(df1.columns)
filter_by_have_numbers=[]
for i in columns_list_df1:
    a=re.findall(r'\d+', i)
    if a:
        filter_by_have_numbers.append(i)


filter_by_2to5 = []
for i in filter_by_have_numbers:
    if 2 <= len(i) <= 5:
        filter_by_2to5.append(i)

df1_without_compounds=df1.drop(columns=filter_by_2to5)

desired_compounds = ["SiO2","P2O5","ZrO2","Na2O","Al2O3","Fe2O3","CaO","MgO","K2O","B2O3","MnO","BaO","ZnO","GeO2","Li2O","Ta2O5","SrO","CdO","SnO2","La2O3","Ga2O3","Y2O3","TiO2","Nb2O5","PbO","HfO2","WO3","Sb2O3","Bi2O3","Cr2O3","Cu2O","BeO","CuO","Nd2O3","CeO2","Cs2O","As2O3","Rb2O","Eu2O3","MoO3","FeO","Mn2O3","ThO2","Ag2O","MnO2","TeO2","Tl2O","CoO","In2O3","Sc2O3","NiO","V2O5","As2O5","Sm2O3","Gd2O3","Tb2O3","Dy2O3","Er2O3","Yb2O3","SnO","Ce2O3","Pr2O3","VO6","Pr6O11","Ni2O3","V2O3","Lu2O3","HgO","Tm2O3","Nb2O3","Tl2O3","Ta2O3","Tb4O7"]
lowercase_desired_compounds = [s.lower() for s in desired_compounds]

filter_by_desired_compounds=[]
for i in filter_by_2to5:
    if i in lowercase_desired_compounds:
        filter_by_desired_compounds.append(i)



df1_compounds_sketch=df1[filter_by_desired_compounds]
semi_filtered_df1=pd.concat([df1_compounds_sketch, df1_without_compounds], axis=1)

filter_by_not_plus=[]
for i in semi_filtered_df1.columns:
    if "+" not in i:
        filter_by_not_plus.append(i)
filtered_df1=semi_filtered_df1[filter_by_not_plus]
extra_fixes1=df1['yo1.5']
extra_fixes2=df1['α1']

filtered_df1['yo1.5']=extra_fixes1
filtered_df1['α1']=extra_fixes2
print(filtered_df1)

filtered_df1.to_csv('output.csv', index=False)