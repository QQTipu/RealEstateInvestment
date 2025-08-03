import pandas as pd
import numpy as np
import streamlit as st

def dvf_fillna_with_med(dvf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Remplisasge des valeurs foncières au m2 nulle par la moyenne de la commune 
    pour remplir les valeurs nulles sans influencer le taux de croisance.
    """
    # Calcul des valeurs de ventes moyennes par commune
    means = dvf_df.groupby('INSEE_C')['VFm2med'].mean().to_dict()
    # Application des valeurs de ventes moyennes sur les valeurs nulles de la commune concernée
    dvf_df['VFm2med'] = dvf_df['VFm2med'].fillna(dvf_df['INSEE_C'].map(means))

    return dvf_df

def dvf_agg_data(dvf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule la mediane de la valeur foncière au m2 par année et code INSEE_C.
    """
    agg_dvf_df = dvf_df[['INSEE_C', 'annee', 'VFm2']]\
                        .groupby(['INSEE_C', 'annee'])\
                        .agg({'VFm2': np.median})\
                        .reset_index()\
                        .sort_values(by=['INSEE_C', 'annee'])
    agg_dvf_df.columns = ['INSEE_C', 'annee', 'VFm2med']

    return agg_dvf_df

def dvf_cleanup_data(dvf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Préparer les données brutes DVF.
    """
    cols_to_keep = ['Date mutation', 'Nature mutation', 'Type local', 'Nombre pieces principales', 'Valeur fonciere', 'Code postal','Commune', 'Code departement', 'Code commune', '1er lot', 'Surface Carrez du 1er lot', 'annee']
    dvf_filtered = dvf_df[(dvf_df['Nature mutation'].str.contains('vente', case=False)) &
                        (dvf_df['Type local'].str.contains('appartement', case=False)) &
                        (dvf_df['Nombre de lots'] == 1) &
                        (dvf_df['Nombre pieces principales'] <= 2.0)
                ]
    # Suppression des lignes qui n'ont pas de vente pour les critères de filtre
    dvf_filtered = dvf_filtered[cols_to_keep].dropna()
    # Création du code INSEE_C
    dvf_filtered['INSEE_C'] = (dvf_filtered['Code departement'].astype(str).str.zfill(2) + dvf_filtered['Code commune'].astype(str).str.zfill(3)).astype('category')
    # Calcul de la valeur foncière au m2
    dvf_filtered['VFm2'] = dvf_filtered['Valeur fonciere'] / dvf_filtered['Surface Carrez du 1er lot']

    return dvf_filtered

@st.cache_data
def dvf_load_data() -> pd.DataFrame:
    """
    Charge les données de valeur foncière (DVF) en DataFrame pandas et mise en cache.
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

    return df

@st.cache_data
def get_dvf_data():
    # Telecharger les DVF
    dvf_df = dvf_load_data()
    # Preparer les données
    clean_dvf_df = dvf_cleanup_data(dvf_df)
    # Aggreger les données par année et commune
    agg_dvf_df = dvf_agg_data(clean_dvf_df)
    # Nettoyage des données nulles
    final_dvf_df = dvf_fillna_with_med(agg_dvf_df)

    return final_dvf_df