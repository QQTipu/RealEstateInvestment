import pandas as pd
import numpy as np
import folium
from folium import plugins
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import requests
import json
from geopy.geocoders import Nominatim
import warnings
warnings.filterwarnings('ignore')

class AnalyseurRentabiliteImmobiliere:
    def __init__(self):
        self.data_dvf = None
        self.data_loyers = None
        self.data_merged = None
        self.geolocator = Nominatim(user_agent="rentabilite_immobiliere")
        
    def charger_donnees(self, fichier_dvf, fichier_loyers):
        """Charge et nettoie les données DVF et loyers"""
        try:
            # Chargement DVF
            self.data_dvf = pd.read_csv(fichier_dvf, sep=';', encoding='latin-1')
            print(f"DVF chargé: {len(self.data_dvf)} lignes")
            
            # Chargement loyers
            self.data_loyers = pd.read_csv(fichier_loyers, sep=';', encoding='latin-1')
            print(f"Loyers chargé: {len(self.data_loyers)} lignes")
            
            return True
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
            return False
    
    def nettoyer_donnees_dvf(self):
        """Nettoie et prépare les données DVF"""
        if self.data_dvf is None:
            return False
            
        # Supprimer la première colonne vide
        self.data_dvf = self.data_dvf.drop(self.data_dvf.columns[0], axis=1)
        
        # Nettoyer les valeurs foncières (remplacer virgule par point)
        self.data_dvf['Valeur fonciere'] = self.data_dvf['Valeur fonciere'].astype(str).str.replace(',', '.')
        self.data_dvf['Valeur fonciere'] = pd.to_numeric(self.data_dvf['Valeur fonciere'], errors='coerce')
        
        # Nettoyer les surfaces
        self.data_dvf['Surface Carrez du 1er lot'] = self.data_dvf['Surface Carrez du 1er lot'].astype(str).str.replace(',', '.')
        self.data_dvf['Surface Carrez du 1er lot'] = pd.to_numeric(self.data_dvf['Surface Carrez du 1er lot'], errors='coerce')
        
        # Filtrer les données valides
        self.data_dvf = self.data_dvf[
            (self.data_dvf['Type local'] == 'Appartement') &
            (self.data_dvf['Valeur fonciere'] > 0) &
            (self.data_dvf['Surface Carrez du 1er lot'] > 0) &
            (self.data_dvf['Valeur fonciere'] < 2000000)  # Filtre aberrants
        ].copy()
        
        # Calculer le prix au m²
        self.data_dvf['prix_m2'] = self.data_dvf['Valeur fonciere'] / self.data_dvf['Surface Carrez du 1er lot']
        
        # Créer code INSEE à 5 chiffres
        self.data_dvf['insee_code'] = (
            self.data_dvf['Code departement'].astype(str).str.zfill(2) + 
            self.data_dvf['Code commune'].astype(str).str.zfill(3)
        )
        
        print(f"DVF nettoyé: {len(self.data_dvf)} appartements valides")
        return True
    
    def nettoyer_donnees_loyers(self):
        """Nettoie et prépare les données de loyers"""
        if self.data_loyers is None:
            return False
            
        # Supprimer la première colonne vide
        self.data_loyers = self.data_loyers.drop(self.data_loyers.columns[0], axis=1)
        
        # Nettoyer les loyers (remplacer virgule par point)
        self.data_loyers['loypredm2'] = self.data_loyers['loypredm2'].astype(str).str.replace(',', '.')
        self.data_loyers['loypredm2'] = pd.to_numeric(self.data_loyers['loypredm2'], errors='coerce')
        
        # Créer code INSEE à 5 chiffres
        self.data_loyers['insee_code'] = self.data_loyers['INSEE_C'].astype(str).str.zfill(5)
        
        # Filtrer les loyers valides
        self.data_loyers = self.data_loyers[
            (self.data_loyers['loypredm2'] > 0) &
            (self.data_loyers['loypredm2'] < 50)  # Filtre aberrants
        ].copy()
        
        print(f"Loyers nettoyé: {len(self.data_loyers)} observations valides")
        return True
    
    def calculer_prix_moyens_par_commune(self):
        """Calcule les prix moyens de vente par commune"""
        if self.data_dvf is None:
            return None
            
        prix_moyens = self.data_dvf.groupby(['insee_code', 'Commune']).agg({
            'prix_m2': ['mean', 'median', 'count'],
            'Valeur fonciere': 'mean',
            'Surface Carrez du 1er lot': 'mean',
            'Code postal': 'first',
            'Code departement': 'first'
        }).round(2)
        
        # Aplatir les colonnes multi-index
        prix_moyens.columns = ['prix_m2_moyen', 'prix_m2_median', 'nb_ventes', 
                              'valeur_moyenne', 'surface_moyenne', 'code_postal', 'departement']
        prix_moyens = prix_moyens.reset_index()
        
        return prix_moyens
    
    def fusionner_donnees(self):
        """Fusionne les données de vente et de location"""
        prix_moyens = self.calculer_prix_moyens_par_commune()
        
        if prix_moyens is None or self.data_loyers is None:
            return False
        
        # Fusion sur le code INSEE
        self.data_merged = pd.merge(
            prix_moyens, 
            self.data_loyers[['insee_code', 'LIBGEO', 'DEP', 'loypredm2']],
            on='insee_code',
            how='inner'
        )
        
        print(f"Données fusionnées: {len(self.data_merged)} communes")
        return True
    
    def calculer_rentabilite(self):
        """Calcule les indices de rentabilité"""
        if self.data_merged is None:
            return False
        
        # Rentabilité brute annuelle (%)
        self.data_merged['rentabilite_brute'] = (
            (self.data_merged['loypredm2'] * 12) / self.data_merged['prix_m2_moyen']
        ) * 100
        
        # Rentabilité nette estimée (85% de la brute)
        self.data_merged['rentabilite_nette'] = self.data_merged['rentabilite_brute'] * 0.85
        
        # Ratio prix/loyer
        self.data_merged['ratio_prix_loyer'] = self.data_merged['prix_m2_moyen'] / self.data_merged['loypredm2']
        
        # Classification de l'attractivité
        conditions = [
            self.data_merged['rentabilite_brute'] >= 8,
            self.data_merged['rentabilite_brute'] >= 6,
            self.data_merged['rentabilite_brute'] >= 4,
            self.data_merged['rentabilite_brute'] >= 2
        ]
        choices = ['Excellente', 'Très bonne', 'Bonne', 'Correcte']
        self.data_merged['attractivite'] = np.select(conditions, choices, 'Faible')
        
        return True
    
    def obtenir_coordonnees_communes(self, echantillon=100):
        """Obtient les coordonnées GPS d'un échantillon de communes"""
        if self.data_merged is None:
            return False
        
        # Prendre un échantillon pour éviter trop de requêtes API
        sample_data = self.data_merged.nlargest(echantillon, 'rentabilite_brute').copy()
        
        coords = []
        for idx, row in sample_data.iterrows():
            try:
                location = self.geolocator.geocode(f"{row['Commune']}, France", timeout=10)
                if location:
                    coords.append({
                        'insee_code': row['insee_code'],
                        'latitude': location.latitude,
                        'longitude': location.longitude
                    })
                    print(f"Géocodage: {row['Commune']} - OK")
                else:
                    print(f"Géocodage: {row['Commune']} - Échec")
            except Exception as e:
                print(f"Erreur géocodage {row['Commune']}: {e}")
                continue
        
        # Fusionner avec les données principales
        coords_df = pd.DataFrame(coords)
        if not coords_df.empty:
            self.data_merged = pd.merge(self.data_merged, coords_df, on='insee_code', how='left')
        
        return True
    
    def creer_carte_rentabilite(self):
        """Crée une carte interactive de la rentabilité"""
        if self.data_merged is None:
            return None
        
        # Filtrer les communes avec coordonnées
        data_carte = self.data_merged.dropna(subset=['latitude', 'longitude'])
        
        if data_carte.empty:
            print("Aucune coordonnée disponible pour la carte")
            return None
        
        # Créer la carte centrée sur la France
        carte = folium.Map(
            location=[46.603354, 1.888334],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Couleurs selon la rentabilité
        def get_color(rentabilite):
            if rentabilite >= 8:
                return 'green'
            elif rentabilite >= 6:
                return 'lightgreen'
            elif rentabilite >= 4:
                return 'orange'
            elif rentabilite >= 2:
                return 'red'
            else:
                return 'darkred'
        
        # Ajouter les marqueurs
        for idx, row in data_carte.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                popup=folium.Popup(f"""
                <b>{row['Commune']}</b><br>
                Prix achat: {row['prix_m2_moyen']:.0f}€/m²<br>
                Loyer: {row['loypredm2']:.1f}€/m²/mois<br>
                <b>Rentabilité brute: {row['rentabilite_brute']:.2f}%</b><br>
                Attractivité: {row['attractivite']}
                """, max_width=300),
                color='black',
                fillColor=get_color(row['rentabilite_brute']),
                fillOpacity=0.8,
                weight=1
            ).add_to(carte)
        
        # Légende
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Rentabilité brute</b></p>
        <p><i class="fa fa-circle" style="color:green"></i> ≥ 8% - Excellente</p>
        <p><i class="fa fa-circle" style="color:lightgreen"></i> 6-8% - Très bonne</p>
        <p><i class="fa fa-circle" style="color:orange"></i> 4-6% - Bonne</p>
        <p><i class="fa fa-circle" style="color:red"></i> 2-4% - Correcte</p>
        <p><i class="fa fa-circle" style="color:darkred"></i> < 2% - Faible</p>
        </div>
        """
        carte.get_root().html.add_child(folium.Element(legend_html))
        
        return carte
    
    def analyser_top_communes(self, n=20):
        """Analyse les meilleures communes pour investir"""
        if self.data_merged is None:
            return None
        
        # Filtrer les communes avec un minimum de données
        data_filtered = self.data_merged[
            (self.data_merged['nb_ventes'] >= 3) &
            (self.data_merged['rentabilite_brute'] > 0)
        ].copy()
        
        # Top communes par rentabilité
        top_communes = data_filtered.nlargest(n, 'rentabilite_brute')
        
        return top_communes[['Commune', 'departement', 'prix_m2_moyen', 'loypredm2', 
                            'rentabilite_brute', 'rentabilite_nette', 'attractivite', 'nb_ventes']]
    
    def creer_graphiques_analyse(self):
        """Crée des graphiques d'analyse"""
        if self.data_merged is None:
            return None
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Distribution de la rentabilité brute',
                'Prix vs Loyer par département',
                'Top 15 communes - Rentabilité',
                'Répartition par attractivité'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Histogramme rentabilité
        fig.add_trace(
            go.Histogram(x=self.data_merged['rentabilite_brute'], nbinsx=50, name='Rentabilité'),
            row=1, col=1
        )
        
        # 2. Scatter plot prix vs loyer
        fig.add_trace(
            go.Scatter(
                x=self.data_merged['prix_m2_moyen'],
                y=self.data_merged['loypredm2'],
                mode='markers',
                text=self.data_merged['Commune'],
                name='Communes',
                marker=dict(size=6, opacity=0.6)
            ),
            row=1, col=2
        )
        
        # 3. Top communes
        top_15 = self.data_merged.nlargest(15, 'rentabilite_brute')
        fig.add_trace(
            go.Bar(
                x=top_15['rentabilite_brute'],
                y=top_15['Commune'],
                orientation='h',
                name='Top communes'
            ),
            row=2, col=1
        )
        
        # 4. Répartition attractivité
        attractivite_counts = self.data_merged['attractivite'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=attractivite_counts.index,
                values=attractivite_counts.values,
                name='Attractivité'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False, title_text="Analyse de Rentabilité Immobilière")
        return fig

    def traitement_complet_avec_progress(self, fichier_dvf, fichier_loyers):
        """Traitement complet avec barre de progression"""
        
        # Créer les éléments de progression
        progress_container = st.container()
        
        with progress_container:
            st.write("### 📈 Progression de l'analyse")
            
            # Barre de progression et status
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Métriques en temps réel
            col1, col2, col3 = st.columns(3)
            
            try:
                # Étape 1 : Chargement DVF (0-20%)
                status_text.text('📁 Chargement du fichier DVF...')
                with col1:
                    st.metric("Étape", "1/6")
                with col2:
                    st.metric("Progression", "0%")
                with col3:
                    st.metric("Statut", "En cours")
                
                self.data_dvf = pd.read_csv(fichier_dvf, sep=';', encoding='latin-1')
                progress_bar.progress(20)
                st.write(f"✅ DVF chargé: {len(self.data_dvf):,} lignes")
                
                # Étape 2 : Chargement loyers (20-35%)
                status_text.text('📁 Chargement du fichier loyers...')
                with col1:
                    st.metric("Étape", "2/6")
                with col2:
                    st.metric("Progression", "20%")
                
                self.data_loyers = pd.read_csv(fichier_loyers, sep=';', encoding='latin-1')
                progress_bar.progress(35)
                st.write(f"✅ Loyers chargé: {len(self.data_loyers):,} lignes")
                
                # Étape 3 : Nettoyage DVF (35-55%)
                status_text.text('🧹 Nettoyage des données DVF...')
                with col1:
                    st.metric("Étape", "3/6")
                with col2:
                    st.metric("Progression", "35%")
                
                self.nettoyer_donnees_dvf()
                progress_bar.progress(55)
                st.write(f"✅ DVF nettoyé: {len(self.data_dvf):,} appartements valides")
                
                # Étape 4 : Nettoyage loyers (55-70%)
                status_text.text('🧹 Nettoyage des données loyers...')
                with col1:
                    st.metric("Étape", "4/6")
                with col2:
                    st.metric("Progression", "55%")
                
                self.nettoyer_donnees_loyers()
                progress_bar.progress(70)
                st.write(f"✅ Loyers nettoyé: {len(self.data_loyers):,} observations valides")
                
                # Étape 5 : Fusion (70-85%)
                status_text.text('🔗 Fusion des données...')
                with col1:
                    st.metric("Étape", "5/6")
                with col2:
                    st.metric("Progression", "70%")
                
                self.fusionner_donnees()
                progress_bar.progress(85)
                st.write(f"✅ Données fusionnées: {len(self.data_merged):,} communes")
                
                # Étape 6 : Calculs (85-100%)
                status_text.text('📊 Calcul des rentabilités...')
                with col1:
                    st.metric("Étape", "6/6")
                with col2:
                    st.metric("Progression", "85%")
                
                self.calculer_rentabilite()
                progress_bar.progress(100)
                
                # Status final
                status_text.text('✅ Analyse terminée avec succès!')
                with col2:
                    st.metric("Progression", "100%")
                with col3:
                    st.metric("Statut", "Terminé")
                
                time.sleep(1)  # Laisser voir le 100%
                
                # Nettoyage des éléments de progression
                progress_bar.empty()
                status_text.empty()
                
                return True
                
            except Exception as e:
                status_text.text(f'❌ Erreur: {str(e)}')
                with col3:
                    st.metric("Statut", "Erreur")
                st.error(f"Erreur lors du traitement: {e}")
                return False

    
    def generer_rapport(self):
        """Génère un rapport de synthèse"""
        if self.data_merged is None:
            return "Aucune donnée disponible"
        
        stats = self.data_merged.describe()
        
        rapport = f"""
    RAPPORT D'ANALYSE DE RENTABILITÉ IMMOBILIÈRE
    ===========================================

    📊 STATISTIQUES GÉNÉRALES
    - Nombre de communes analysées: {len(self.data_merged)}
    - Prix moyen d'achat: {self.data_merged['prix_m2_moyen'].mean():.0f}€/m²
    - Loyer moyen: {self.data_loyers['loypredm2'].mean():.2f}€/m²/mois
    - Rentabilité brute moyenne: {self.data_merged['rentabilite_brute'].mean():.2f}%

    🏆 MEILLEURES OPPORTUNITÉS (Top 5)
    """
        
        top_5 = self.data_merged.nlargest(5, 'rentabilite_brute')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            # Convertir le département en entier si c'est une string
            dept = str(row['departement']).zfill(2) if isinstance(row['departement'], (int, float, str)) else row['departement']
            
            rapport += f"""
    {i}. {row['Commune']} ({dept})
    💰 Prix: {row['prix_m2_moyen']:.0f}€/m² | Loyer: {row['loypredm2']:.1f}€/m²
    📈 Rentabilité: {row['rentabilite_brute']:.2f}% | Attractivité: {row['attractivite']}
    """
        
        rapport += f"""
    📊 RÉPARTITION PAR ATTRACTIVITÉ
    {self.data_merged['attractivite'].value_counts().to_string()}

    ⚠️ NOTES IMPORTANTES
    - Ces calculs sont basés sur des données moyennes
    - La rentabilité réelle dépend de nombreux facteurs (charges, vacance, travaux...)
    - Il est recommandé de faire une étude détaillée avant tout investissement
    - Les données de loyer sont des estimations prédictives
    """
    
        return rapport

# Interface Streamlit
def main():
    st.set_page_config(
        page_title="Analyseur de Rentabilité Immobilière",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 Analyseur de Rentabilité Immobilière")
    st.markdown("*Analysez la rentabilité des investissements immobiliers en France*")
    
    # Sidebar pour les paramètres
    st.sidebar.header("📁 Chargement des données")
    
    fichier_dvf = st.sidebar.file_uploader("Fichier DVF (ventes)", type=['csv'])
    fichier_loyers = st.sidebar.file_uploader("Fichier Loyers", type=['csv'])
    
    if fichier_dvf and fichier_loyers:
        # Initialiser l'analyseur
        analyseur = AnalyseurRentabiliteImmobiliere()
        
        # Chargement et traitement des données
        with st.spinner("Chargement et traitement des données..."):
            if analyseur.charger_donnees(fichier_dvf, fichier_loyers):
                analyseur.nettoyer_donnees_dvf()
                analyseur.nettoyer_donnees_loyers()
                analyseur.fusionner_donnees()
                analyseur.calculer_rentabilite()
        
        if analyseur.data_merged is not None:
            st.success(f"✅ Analyse terminée - {len(analyseur.data_merged)} communes analysées")
            
            # Onglets principaux
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Synthèse", "🗺️ Carte", "📈 Graphiques", "📋 Rapport"])
            
            with tab1:
                st.header("Synthèse des résultats")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Communes analysées", len(analyseur.data_merged))
                with col2:
                    st.metric("Prix moyen/m²", f"{analyseur.data_merged['prix_m2_moyen'].mean():.0f}€")
                with col3:
                    st.metric("Loyer moyen/m²", f"{analyseur.data_merged['loypredm2'].mean():.1f}€")
                with col4:
                    st.metric("Rentabilité moyenne", f"{analyseur.data_merged['rentabilite_brute'].mean():.2f}%")
                
                st.subheader("🏆 Top 20 des meilleures communes pour investir")
                top_communes = analyseur.analyser_top_communes(20)
                if top_communes is not None:
                    st.dataframe(
                        top_communes.style.format({
                            'prix_m2_moyen': '{:.0f}€',
                            'loypredm2': '{:.1f}€',
                            'rentabilite_brute': '{:.2f}%',
                            'rentabilite_nette': '{:.2f}%'
                        }),
                        use_container_width=True
                    )
            
            with tab2:
                st.header("🗺️ Carte de rentabilité")
                
                # Option pour géocoder
                if st.button("🌍 Générer la carte (géocodage des communes)"):
                    with st.spinner("Géocodage en cours... (peut prendre quelques minutes)"):
                        analyseur.obtenir_coordonnees_communes(50)  # Limité à 50 pour éviter timeout
                        carte = analyseur.creer_carte_rentabilite()
                        
                        if carte:
                            st.success("Carte générée avec succès!")
                            # Note: Dans Streamlit, vous devriez utiliser folium_static pour afficher la carte
                            # st.components.v1.html(carte._repr_html_(), height=600)
                            st.info("Carte générée - utilisez folium_static pour l'affichage dans Streamlit")
                        else:
                            st.error("Impossible de générer la carte")
            
            with tab3:
                st.header("📈 Analyses graphiques")
                
                fig = analyseur.creer_graphiques_analyse()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                st.header("📋 Rapport détaillé")
                
                rapport = analyseur.generer_rapport()
                st.text(rapport)
                
                # Bouton de téléchargement du rapport
                st.download_button(
                    label="📥 Télécharger le rapport",
                    data=rapport,
                    file_name="rapport_rentabilite_immobiliere.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    # Pour utilisation en ligne de commande
    analyseur = AnalyseurRentabiliteImmobiliere()
    
    # Chargement des données
    if analyseur.charger_donnees('./data/dvf.csv', './data/loyers.csv'):
        print("✅ Données chargées")
        
        # Nettoyage
        analyseur.nettoyer_donnees_dvf()
        analyseur.nettoyer_donnees_loyers()
        
        # Fusion et calculs
        if analyseur.fusionner_donnees():
            analyseur.calculer_rentabilite()
            
            # Analyses
            print("\n📊 ANALYSE TERMINÉE")
            print(f"Communes analysées: {len(analyseur.data_merged)}")
            
            # Top communes
            top_communes = analyseur.analyser_top_communes(10)
            print("\n🏆 TOP 10 COMMUNES:")
            print(top_communes.to_string(index=False))
            
            # Sauvegarde des résultats
            analyseur.data_merged.to_csv('resultats_rentabilite.csv', index=False, sep=';')
            print("\n💾 Résultats sauvegardés dans 'resultats_rentabilite.csv'")
            
            # Rapport
            rapport = analyseur.generer_rapport()
            with open('rapport_rentabilite.txt', 'w', encoding='utf-8') as f:
                f.write(rapport)
            print("📋 Rapport sauvegardé dans 'rapport_rentabilite.txt'")
        else:
            print("❌ Erreur lors de la fusion des données")
    else:
        print("❌ Erreur lors du chargement des données")