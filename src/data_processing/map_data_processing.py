import pandas as pd
import streamlit as st

from src.data.data_dl_url import COMMUNE_GEOCODED_URL

def geocode_df(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Géocode le dataframe joint des DVF et des loyers à partir du code commune INSEE
    et du libellé de commune.
    """
    comm_df = merged_df[['INSEE_C', 'LIBGEO', 'loypredm2', 'prof_rate']].drop_duplicates()
    geocoded_df = pd.read_csv(COMMUNE_GEOCODED_URL['2025'], encoding='utf-8', sep=',', decimal='.')
    geocoded_comm_df = comm_df.merge(geocoded_df[['code_commune_insee', 'latitude', 'longitude']],
                                     left_on='INSEE_C',
                                     right_on='code_commune_insee',
                                     how='left')
    geocoded_comm_df['prof_rate'] = geocoded_comm_df['prof_rate'].astype('float64')

    return geocoded_comm_df

def calculate_prof_rate_color(prof_rate: float) -> str:
    """
    Retourne une couleur en fonction du taux de profitabilité.
    """
    if prof_rate < 4.0:
        return '#ff0000'
    elif prof_rate < 8.0:
        return '#e3ba54'
    else:
        return '#32a852'
    
@st.cache_data
def get_geocoded_data(merged_df: pd.DataFrame) -> pd.DataFrame:
    # Géocoder les données mergées
    geocoded_df = geocode_df(merged_df)
    # Supprimer les lignes sans coordonnées géographiques
    geocoded_df = geocoded_df.dropna(subset=['latitude', 'longitude'])
    # Ajouter une colonne de couleur en fonction du taux de profitabilité
    geocoded_df['prof_rate_color'] = geocoded_df['prof_rate'].apply(calculate_prof_rate_color)
    return geocoded_df