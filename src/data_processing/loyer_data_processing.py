import pandas as pd
import numpy as np
import streamlit as st

from src.data.data_dl_url import LOYERS_URL

def loyer_cleanup_data(loyers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Préparer les données brutes des loyers.
    """
    loyers_df = loyers_df[['INSEE_C', 'LIBGEO', 'annee', 'loypredm2', 'lwr.IPm2', 'upr.IPm2']].sort_values(['INSEE_C', 'annee'])
    loyers_df['INSEE_C'] = loyers_df['INSEE_C'].astype('category')

    return loyers_df

@st.cache_data
def loyer_load_data() -> pd.DataFrame:
    """
    Charge les données des loyers en DataFrame pandas et mise en cache.
    """
    loyers_df = pd.read_csv(LOYERS_URL['2024'], encoding='latin-1', sep=';', decimal=',')
    loyers_df['annee'] = '2024'
    
    return loyers_df

@st.cache_data
def get_loyer_data():
    # Telecharger les données des loyers
    loyers_df = loyer_load_data()
    # Préparer les données
    clean_loyer_df = loyer_cleanup_data(loyers_df)

    return clean_loyer_df