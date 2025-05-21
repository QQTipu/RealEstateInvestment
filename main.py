# Dashboard de rentabilité immobilière par département et type de logement

import pandas as pd
import ipywidgets as widgets
from IPython.display import display
import plotly.express as px

# Fonction simulée pour récupérer le prix d'achat moyen au m²
def get_prix_achat(departement, typologie):
    # Remplacer par appel à une API ou base de données réelle
    prix_fictifs = {
        ("Paris", "T2"): 11000,
        ("Paris", "T3"): 10500,
        ("Rhône", "T2"): 5000,
        ("Rhône", "T3"): 4700,
    }
    return prix_fictifs.get((departement, typologie), 0)

# Fonction simulée pour récupérer le loyer mensuel moyen au m²
def get_loyer_m2(departement, typologie):
    loyers_fictifs = {
        ("Paris", "T2"): 33,
        ("Paris", "T3"): 30,
        ("Rhône", "T2"): 18,
        ("Rhône", "T3"): 17,
    }
    return loyers_fictifs.get((departement, typologie), 0)

# Calcul de la rentabilité brute annuelle (%)
def calcul_rentabilite(prix_achat_m2, loyer_mensuel_m2):
    if prix_achat_m2 == 0:
        return 0
    return round((loyer_mensuel_m2 * 12 / prix_achat_m2) * 100, 2)

# Interface utilisateur
liste_departements = ["Paris", "Rhône"]
liste_typologies = ["T2", "T3"]

select_departement = widgets.Dropdown(options=liste_departements, description="Département:")
select_typologie = widgets.Dropdown(options=liste_typologies, description="Typologie:")

def afficher_resultats(departement, typologie):
    prix_achat = get_prix_achat(departement, typologie)
    loyer = get_loyer_m2(departement, typologie)
    rentabilite = calcul_rentabilite(prix_achat, loyer)

    df = pd.DataFrame({
        "Indicateur": ["Prix achat / m²", "Loyer / m² / mois", "Rentabilité brute annuelle %"],
        "Valeur": [prix_achat, loyer, rentabilite]
    })
    
    display(df)
    fig = px.bar(df, x="Indicateur", y="Valeur", text="Valeur", title=f"Analyse - {departement}, {typologie}", color="Indicateur")
    fig.show()

ui = widgets.VBox([select_departement, select_typologie])
out = widgets.interactive_output(afficher_resultats, {
    "departement": select_departement,
    "typologie": select_typologie
})

display(ui, out)
