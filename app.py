import pandas as pd
import numpy as np
import streamlit as st
from src.data_processing import dvf_load_data

def main():
    st.set_page_config(
        page_title="Mon App",
        page_icon="📊",
        layout="wide"
    )

    st.title("🏠 Accueil")
    st.write("Bienvenue dans mon application Streamlit!")

    df_dvf = dvf_load_data()
    st.dataframe(df_dvf.head(100))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite: {str(e)}")
        # Mode debug (optionnel)
        if st.checkbox("🔧 Afficher les détails de l'erreur"):
            st.exception(e) 