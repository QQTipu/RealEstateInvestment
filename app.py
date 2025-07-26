import streamlit as st

def main():
    st.title("📊 Investissement immobilier")
    st.markdown("---")
    return

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite: {str(e)}")
        # Mode debug (optionnel)
        if st.checkbox("🔧 Afficher les détails de l'erreur"):
            st.exception(e)