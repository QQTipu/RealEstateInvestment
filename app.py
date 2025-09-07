import pandas as pd
import numpy as np
import streamlit as st

from src.data_processing.dvf_data_processing import get_dvf_data
from src.data_processing.loyer_data_processing import get_loyer_data
from src.data_processing.real_estate_calculation import get_calc_data
from src.data_processing.map_data_processing import geocode_df

def footer():
    st.markdown('---')
    st.markdown('*Application réalisé avec :streamlit: [Streamlit](https://streamlit.io/) par T. Fortuné.*')
    st.markdown('''Calculs réalisés à partir des données :  
        - [Carte des loyers](https://www.data.gouv.fr/datasets/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2024/) - Ministère de la Transition écologique  
        - [Demandes de valeurs foncières](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres/) - Ministère de l'Economie, des Finances et de l'Industrie
        ''')

def tab_map():
    dvf_df = get_dvf_data()
    loyers_df = get_loyer_data()
    merged_df = get_calc_data(dvf_df, loyers_df)
    geocoded_df = geocode_df(merged_df).dropna(subset=['latitude', 'longitude'])
    st.write(geocoded_df.dtypes)  # Affiche le pour

    st.map(geocoded_df,
           latitude='latitude',
           longitude='longitude',
           color='prof_rate'
           )
    return

def tab_simulation():
    dvf_df = get_dvf_data()
    loyers_df = get_loyer_data()

    interest_rate = st.slider("Taux d'intérêt", min_value=0.0, max_value=10.0, value=3.0, format="%0.2f")
    commune = st.selectbox("Commune du bien", loyers_df['LIBGEO'])
    loyer_m2 = loyers_df[loyers_df['LIBGEO'] == commune]['loypredm2'].values[0]

    st.write(f"Taux d'intérêt: {interest_rate}%")
    st.write(f"Loyer au m² à {commune} : {loyer_m2} €/m²")
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

    st.write("Données géocodées")
    geocoded_df = geocode_df(merged_df)
    st.dataframe(geocoded_df.head(1000))

def main():
    st.set_page_config(
        page_title="APP - Investissement immobilier",
        page_icon="./style/favicon-ImmoStats.png",
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