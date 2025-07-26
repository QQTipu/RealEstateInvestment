import pandas as pd
import numpy as np
import streamlit as st

def dvf_cleanup_data(dvf_df: pd.DataFrame):
    """
    Préparer les données brutes DVF.
    """
    cols_to_keep = ['Date mutation', 'Nature mutation', 'Type local', 'Nombre pieces principales', 'Valeur fonciere', 'Code postal','Commune', 'Code departement', 'Code commune', '1er lot', 'Surface Carrez du 1er lot', 'annee']
    dvf_filtered = dvf_df[(dvf_df['Nature mutation'].str.contains('vente', case=False)) &
                        (dvf_df['Type local'].str.contains('appartement', case=False)) &
                        (dvf_df['Nombre de lots'] == 1) &
                        (dvf_df['Nombre pieces principales'] <= 2.0)
                ]

    dvf_filtered = dvf_filtered[cols_to_keep].dropna()
    return dvf_filtered

@st.cache_data
def dvf_load_data() -> pd.DataFrame:
    """
    Chargement des données DVF en dataframe pandas et mise en cache.
    """
    urls_dict = {
        '2020': 'https://www.data.gouv.fr/api/1/datasets/r/0d16005c-f68e-487c-811b-0deddba0c3f1',
        '2021': 'https://www.data.gouv.fr/api/1/datasets/r/3942b268-04e7-4202-b96d-93b9ef6254d6',
        '2022': 'https://www.data.gouv.fr/api/1/datasets/r/b4f43708-c5a8-4f30-80dc-7adfa1265d74',
        '2023': 'https://www.data.gouv.fr/api/1/datasets/r/bc213c7c-c4d4-4385-bf1f-719573d39e90',
        '2024': 'https://www.data.gouv.fr/api/1/datasets/r/5ffa8553-0e8f-4622-add9-5c0b593ca1f8'
        }

    df_list = []
    for year in urls_dict:
        print(f"year : {year}, url: {urls_dict.get(year)}")
        df_year = pd.read_csv(urls_dict.get(year), compression='zip', encoding='latin-1', sep='|', decimal=',')
        df_year['annee'] = year

        df_list.append(df_year)
    
    df = pd.concat(df_list)
    return dvf_cleanup_data(df)

def get_dvf_data():
    
    return