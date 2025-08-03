import pandas as pd
import streamlit as st

def merge_dvf_loyer(dvf_df: pd.DataFrame, loyer_df: pd.DataFrame) -> pd.DataFrame:
    """
    Joint les deux dataframe de loyer et de DVF sur le code insee de la commune 'INSEE_C'.
    """
    loyer_df = loyer_df[['INSEE_C', 'LIBGEO', 'loypredm2', 'lwr.IPm2', 'upr.IPm2']]
    merged_df = dvf_df.merge(loyer_df, how='left', on='INSEE_C')
    return merged_df

def calculate_profitability(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule de taux de retabilité brut en pourcentage.
    """
    calc_df = merged_df.copy()
    calc_df['prof_rate'] = ((calc_df['loypredm2'] * 12) / calc_df['VFm2med']) * 100
    return calc_df

@st.cache_data
def get_calc_data(dvf_df: pd.DataFrame, loyer_df: pd.DataFrame) -> pd.DataFrame:
    # Merger les données des loyers et des DVF
    merged_df = merge_dvf_loyer(dvf_df, loyer_df)
    # Calculer le taux de rentabilité
    calc_df = calculate_profitability(merged_df)

    return calc_df