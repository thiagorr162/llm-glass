import json
import pandas as pd
from pathlib import Path
import re

import pandas as pd

def convert_to_mol(dataframe, json_data):
    # descartei do dataframe as linhas com tipo none
    dataframe = dataframe[~dataframe["type"].str.lower().eq("none")]

    # separei as linhas com tipo molar
    Already_mol = dataframe[dataframe["type"].str.lower().eq("molar")]
    dataframe = dataframe[~dataframe["type"].str.lower().eq("molar")]

    # criei um dataframe só com compostos
    compound_columns = [compound for compound in json_data if compound in dataframe.columns]
    compounds_df = dataframe[compound_columns].copy()

    other_columns = [col for col in dataframe.columns if col not in compound_columns]
    other_columns_df = dataframe[other_columns].copy()

    # pega as massas molares do dicionario do json
    molar_masses = {
        compound: json_data[compound]["molar_mass"]
        for compound in compound_columns
    }

    # essa lista serve pra armazenar o total de mols sem mexer nos mols individuais de cada elemento
    total_mols = []

    for line_index, row in compounds_df.iterrows():
        # armazena a quantidade de mols de cada elemento
        mols_per_row = []

        # faz as contas de quantos mols tem de cada elemento e adiciona na lista mols_per_row
        for compound_col, value in row.items():
            mols = value / molar_masses[compound_col] 
            mols_per_row.append(mols)

        # soma os mols de todos os elementos e joga na lista total_mols
        total_mols_in_row = sum(mols_per_row)
        total_mols.append(total_mols_in_row)

        # converte de % de massa pra % de mol
        for i, compound_col in enumerate(compound_columns):
            mol_percent = round((mols_per_row[i] / total_mols_in_row) * 100, 2)
            compounds_df.loc[line_index, compound_col] = mol_percent

    # junta as colunas não compostas ao DataFrame de compostos
    final_df = pd.concat([compounds_df, other_columns_df], axis=1)

    # junta os dataframes
    final_df = pd.concat([final_df, Already_mol], axis=0, ignore_index=True)

    # excluir de novo linhas com type = none
    final_df = final_df[~final_df["type"].str.lower().eq("none")]

    # deletar de novo a coluna type
    final_df = final_df.drop(columns=["type"])

    return final_df

def convert_to_massic(dataframe, json_data):
    # descartei do dataframe as linhas com tipo none
    dataframe = dataframe[~dataframe["type"].str.lower().eq("none")]

    # separei as linhas com tipo massic
    Already_massic = dataframe[dataframe["type"].str.lower().eq("massic")]
    dataframe = dataframe[~dataframe["type"].str.lower().eq("massic")]

    # criei um dataframe só com compostos
    compound_columns = [compound for compound in json_data if compound in dataframe.columns]
    compounds_df = dataframe[compound_columns].copy()

    other_columns = [col for col in dataframe.columns if col not in compound_columns]
    other_columns_df = dataframe[other_columns].copy()

    # pega as massas molares do dicionário do json
    molar_masses = {
        compound: json_data[compound]["molar_mass"]
        for compound in compound_columns
    }

    # essa lista serve pra armazenar o total de massa sem mexer nas massas individuais
    total_mass = []

    for line_index, row in compounds_df.iterrows():
        # armazena a quantidade de massa de cada elemento
        mass_per_row = []

        # faz as contas de quanta massa tem de cada elemento e adiciona na lista mass_per_row
        for compound_col, value in row.items():
            mass = value * molar_masses[compound_col] 
            mass_per_row.append(mass)

        # soma as massas de todos os elementos e joga na lista total_mols
        total_mass_in_row = sum(mass_per_row)
        total_mass.append(total_mass_in_row)

        # converte de % de mol pra % de massa
        for i, compound_col in enumerate(compound_columns):
            mass_percent = round((mass_per_row[i] / total_mass_in_row) * 100, 2)
            compounds_df.loc[line_index, compound_col] = mass_percent

    # junta as colunas não compostas ao DataFrame de compostos
    final_df = pd.concat([compounds_df, other_columns_df], axis=1)

    # junta os dataframes
    final_df = pd.concat([final_df, Already_massic], axis=0, ignore_index=True)

    # exclui de novo linhas com type = none
    final_df = final_df[~final_df["type"].str.lower().eq("none")]

    # deleta a coluna type
    final_df = final_df.drop(columns=["type"])

    return final_df


if __name__ == "__main__":

    # Caminhos
    filtered_path = Path("data/filtered")
    json_path = Path("json/properties.json")
    input_csv = filtered_path / "FINAL_compounds_and_refractive.csv"

    # Carrega o JSON
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    desired_compounds_info = data["desired_compounds_info"]

    # Carrega o DataFrame
    df = pd.read_csv(input_csv)

    # Executa as conversões
    mol_df = convert_to_mol(df, desired_compounds_info)
    massic_df = convert_to_massic(df, desired_compounds_info)

    # Salva os arquivos resultantes
    mol_output_path = filtered_path / "MOL_FINAL_dataframe.csv"
    massic_output_path = filtered_path / "MASSIC_FINAL_dataframe.csv"

    mol_df.to_csv(mol_output_path, index=False)
    massic_df.to_csv(massic_output_path, index=False)
    print("operaçao concluida")




