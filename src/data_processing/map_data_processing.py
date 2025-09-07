import pandas as pd
import streamlit as st

from src.data.data_dl_url import COMMUNE_GEOCODED_URL

@st.cache_data
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
    
    return geocoded_comm_df