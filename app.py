import pandas as pd
import numpy as np
import streamlit as st

from src.data_processing.dvf_data_processing import get_dvf_data
from src.data_processing.loyer_data_processing import get_loyer_data
from src.data_processing.real_estate_calculation import get_calc_data

def footer():
    st.markdown('---')
    st.markdown('*Application réalisé avec :streamlit: [Streamlit](https://streamlit.io/) par T. Fortuné.*')
    st.markdown('''Calculs réalisés à partir des données :  
        - [Carte des loyers](https://www.data.gouv.fr/datasets/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2024/) - Ministère de la Transition écologique  
        - [Demandes de valeurs foncières](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres/) - Ministère de l'Economie, des Finances et de l'Industrie
        ''')

def tab_map():
    st.map()
    return

def tab_simulation():
    return

def tab_rawdata():
    st.write("Données DVF")
    dvf_df = get_dvf_data()
    st.dataframe(dvf_df.head(1000))

    st.write("Données de loyers")
    loyers_df = get_loyer_data()
    st.dataframe(loyers_df.head(1000))

    st.write("Données mergées")
    merged_df = get_calc_data(dvf_df, loyers_df)
    st.dataframe(merged_df.head(1000))

def main():
    st.set_page_config(
        page_title="APP - Investissement immobilier",
        page_icon="📊",
        layout="wide"
    )

    st.title("🏠 Marché immobilier")
    st.write("Bienvenue dans mon application Streamlit!")

    tab1, tab2, tab3 = st.tabs(["Carte de rentabilité", "Simulation de rentabilité", "Données brutes"])
    with tab1:
        tab_map()
    with tab2:
        tab_simulation()
    with tab3:
        tab_rawdata()

    footer()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite: {str(e)}")
        # Mode debug (optionnel)
        if st.checkbox("🔧 Afficher les détails de l'erreur"):
            st.exception(e) 