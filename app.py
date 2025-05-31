import pandas as pd
import numpy as np
import folium
from folium import plugins
import requests
import json
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class RealEstateAnalyzer:
    def __init__(self):
        self.data = None
        self.map_france = None
        
    def load_sample_data(self):
        """Charge des données d'exemple pour les principales villes françaises"""
        # Données d'exemple basées sur des moyennes approximatives (à remplacer par de vraies données)
        cities_data = {
            'ville': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 
                     'Montpellier', 'Strasbourg', 'Bordeaux', 'Lille', 'Rennes', 
                     'Reims', 'Saint-Étienne', 'Toulon', 'Le Havre', 'Grenoble',
                     'Dijon', 'Angers', 'Nîmes', 'Villeurbanne'],
            'latitude': [48.8566, 45.7640, 43.2965, 43.6047, 43.7102, 47.2184,
                        43.6110, 48.5734, 44.8378, 50.6292, 48.1173, 49.2583,
                        45.4397, 43.1242, 49.4944, 45.1885, 47.3220, 47.4784,
                        43.8367, 45.7797],
            'longitude': [2.3522, 4.8357, 5.3698, 1.4442, 7.2619, -1.5536,
                         3.8767, 7.7521, -0.5792, 3.0573, -1.6778, 4.0317,
                         4.3872, 5.9280, 0.1079, 5.7245, 5.0415, -0.5632,
                         4.3601, 4.8732],
            'prix_achat_m2': [11000, 4500, 3800, 3200, 4800, 3500, 3400, 3300, 4200,
                             2800, 3600, 2200, 1800, 3500, 2100, 3200, 2900, 2600,
                             2400, 4000],
            'loyer_m2_mois': [30, 13, 12, 11, 16, 12, 12, 12, 14, 10, 12, 8, 7,
                             12, 8, 11, 10, 9, 9, 13],
            'population': [2161000, 515695, 870731, 479553, 340017, 314138,
                          285121, 280966, 257068, 232787, 217728, 182592,
                          171057, 176198, 170147, 158552, 156920, 154508,
                          148561, 149019]
        }
        
        self.data = pd.DataFrame(cities_data)
        self.calculate_profitability_metrics()
        
    def calculate_profitability_metrics(self):
        """Calcule les différents indices de rentabilité"""
        # Rentabilité brute annuelle
        self.data['loyer_annuel_m2'] = self.data['loyer_m2_mois'] * 12
        self.data['rentabilite_brute'] = (self.data['loyer_annuel_m2'] / self.data['prix_achat_m2']) * 100
        
        # Rentabilité nette (estimation avec 20% de charges)
        self.data['rentabilite_nette'] = self.data['rentabilite_brute'] * 0.8
        
        # Cash-flow pour un appartement de 50m²
        surface_type = 50
        self.data['prix_achat_total'] = self.data['prix_achat_m2'] * surface_type
        self.data['loyer_mensuel_total'] = self.data['loyer_m2_mois'] * surface_type
        self.data['loyer_annuel_total'] = self.data['loyer_mensuel_total'] * 12
        
        # Calcul du cash-flow (estimation avec emprunt à 80% sur 20 ans à 3.5%)
        taux_emprunt = 0.035
        duree_emprunt = 20
        pourcentage_emprunt = 0.8
        
        self.data['montant_emprunt'] = self.data['prix_achat_total'] * pourcentage_emprunt
        self.data['mensualite_emprunt'] = self.calculate_monthly_payment(
            self.data['montant_emprunt'], taux_emprunt, duree_emprunt
        )
        self.data['cash_flow_mensuel'] = (self.data['loyer_mensuel_total'] * 0.8) - self.data['mensualite_emprunt']
        
        # Temps de retour sur investissement (apport initial)
        self.data['apport_initial'] = self.data['prix_achat_total'] * (1 - pourcentage_emprunt)
        self.data['temps_retour_annees'] = self.data['apport_initial'] / (self.data['cash_flow_mensuel'] * 12)
        
        # Score global de rentabilité (pondération des différents critères)
        self.data['score_rentabilite'] = (
            self.data['rentabilite_brute'] * 0.4 +
            (self.data['cash_flow_mensuel'] / 100) * 0.3 +
            (10 / self.data['temps_retour_annees']) * 0.3
        )
    
    def calculate_monthly_payment(self, principal, annual_rate, years):
        """Calcule la mensualité d'un emprunt"""
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        if monthly_rate == 0:
            return principal / num_payments
        return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    def create_interactive_map(self):
        """Crée une carte interactive avec les données de rentabilité"""
        # Centre de la France
        center_lat, center_lon = 46.2276, 2.2137
        
        # Créer la carte
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Normaliser les scores pour les couleurs
        min_score = self.data['score_rentabilite'].min()
        max_score = self.data['score_rentabilite'].max()
        
        # Ajouter les marqueurs pour chaque ville
        for idx, row in self.data.iterrows():
            # Couleur basée sur le score de rentabilité
            score_norm = (row['score_rentabilite'] - min_score) / (max_score - min_score)
            if score_norm > 0.7:
                color = 'green'
                icon = 'arrow-up'
            elif score_norm > 0.4:
                color = 'orange'
                icon = 'minus'
            else:
                color = 'red'
                icon = 'arrow-down'
            
            # Popup avec les informations détaillées
            popup_text = f"""
            <b>{row['ville']}</b><br>
            Prix d'achat: {row['prix_achat_m2']:,.0f} €/m²<br>
            Loyer: {row['loyer_m2_mois']:.0f} €/m²/mois<br>
            <b>Rentabilité brute: {row['rentabilite_brute']:.1f}%</b><br>
            Rentabilité nette: {row['rentabilite_nette']:.1f}%<br>
            Cash-flow mensuel (50m²): {row['cash_flow_mensuel']:.0f} €<br>
            Temps de retour: {row['temps_retour_annees']:.1f} ans<br>
            <b>Score global: {row['score_rentabilite']:.1f}</b>
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{row['ville']} - Rentabilité: {row['rentabilite_brute']:.1f}%",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(m)
        
        # Ajouter une légende
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Légende Rentabilité</h4>
        <p><i class="fa fa-arrow-up" style="color:green"></i> Excellente (>70%)</p>
        <p><i class="fa fa-minus" style="color:orange"></i> Moyenne (40-70%)</p>
        <p><i class="fa fa-arrow-down" style="color:red"></i> Faible (<40%)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def create_comparison_charts(self):
        """Crée des graphiques de comparaison"""
        # Graphique 1: Rentabilité vs Prix d'achat
        fig1 = px.scatter(
            self.data, 
            x='prix_achat_m2', 
            y='rentabilite_brute',
            size='population',
            color='score_rentabilite',
            hover_name='ville',
            title="Rentabilité Brute vs Prix d'Achat",
            labels={
                'prix_achat_m2': 'Prix d\'achat (€/m²)',
                'rentabilite_brute': 'Rentabilité brute (%)',
                'score_rentabilite': 'Score'
            },
            color_continuous_scale='RdYlGn'
        )
        
        # Graphique 2: Top 10 des villes par rentabilité
        top_cities = self.data.nlargest(10, 'rentabilite_brute')
        fig2 = px.bar(
            top_cities,
            x='rentabilite_brute',
            y='ville',
            orientation='h',
            title="Top 10 - Rentabilité Brute",
            labels={'rentabilite_brute': 'Rentabilité brute (%)'},
            color='rentabilite_brute',
            color_continuous_scale='RdYlGn'
        )
        fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        # Graphique 3: Cash-flow mensuel
        fig3 = px.bar(
            self.data.sort_values('cash_flow_mensuel', ascending=True),
            x='cash_flow_mensuel',
            y='ville',
            orientation='h',
            title="Cash-flow Mensuel par Ville (appartement 50m²)",
            labels={'cash_flow_mensuel': 'Cash-flow mensuel (€)'},
            color='cash_flow_mensuel',
            color_continuous_scale='RdYlGn'
        )
        fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        return fig1, fig2, fig3
    
    def get_investment_summary(self):
        """Retourne un résumé des meilleures opportunités"""
        # Top 5 par rentabilité brute
        top_rentability = self.data.nlargest(5, 'rentabilite_brute')[['ville', 'rentabilite_brute', 'prix_achat_m2']]
        
        # Top 5 par cash-flow
        top_cashflow = self.data.nlargest(5, 'cash_flow_mensuel')[['ville', 'cash_flow_mensuel', 'loyer_mensuel_total']]
        
        # Top 5 par score global
        top_score = self.data.nlargest(5, 'score_rentabilite')[['ville', 'score_rentabilite', 'rentabilite_brute', 'cash_flow_mensuel']]
        
        return {
            'top_rentability': top_rentability,
            'top_cashflow': top_cashflow,
            'top_score': top_score
        }

def main():
    st.set_page_config(page_title="Analyseur Rentabilité Immobilière", layout="wide")
    
    st.title("🏠 Analyseur de Rentabilité Immobilière - France")
    st.markdown("### Comparaison des opportunités d'investissement immobilier")
    
    # Initialiser l'analyseur
    analyzer = RealEstateAnalyzer()
    
    # Sidebar pour les paramètres
    st.sidebar.header("Paramètres d'Analyse")
    surface_appartement = st.sidebar.slider("Surface de l'appartement (m²)", 20, 100, 50)
    taux_emprunt = st.sidebar.slider("Taux d'emprunt (%)", 1.0, 6.0, 3.5) / 100
    apport_personnel = st.sidebar.slider("% d'apport personnel", 10, 50, 20)
    
    # Charger les données
    with st.spinner("Chargement des données..."):
        analyzer.load_sample_data()
    
    # Tabs pour organiser l'interface
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte Interactive", "📊 Graphiques", "📈 Classements", "💡 Recommandations"])
    
    with tab1:
        st.subheader("Carte de Rentabilité par Ville")
        st.markdown("*Cliquez sur les marqueurs pour voir les détails*")
        
        # Créer et afficher la carte
        map_france = analyzer.create_interactive_map()
        st.components.v1.html(map_france._repr_html_(), height=600)
        
    with tab2:
        st.subheader("Analyses Comparatives")
        
        # Créer les graphiques
        fig1, fig2, fig3 = analyzer.create_comparison_charts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.plotly_chart(fig2, use_container_width=True)
        
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab3:
        st.subheader("Classements et Données Détaillées")
        
        # Obtenir le résumé
        summary = analyzer.get_investment_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏆 Top 5 - Rentabilité Brute**")
            st.dataframe(summary['top_rentability'].round(1))
        
        with col2:
            st.markdown("**💰 Top 5 - Cash-flow Mensuel**")
            st.dataframe(summary['top_cashflow'].round(0))
        
        with col3:
            st.markdown("**⭐ Top 5 - Score Global**")
            st.dataframe(summary['top_score'].round(1))
        
        # Tableau complet
        st.subheader("Données Complètes")
        display_columns = ['ville', 'prix_achat_m2', 'loyer_m2_mois', 'rentabilite_brute', 
                          'rentabilite_nette', 'cash_flow_mensuel', 'score_rentabilite']
        st.dataframe(analyzer.data[display_columns].round(1), use_container_width=True)
    
    with tab4:
        st.subheader("💡 Recommandations d'Investissement")
        
        best_overall = analyzer.data.loc[analyzer.data['score_rentabilite'].idxmax()]
        best_rentability = analyzer.data.loc[analyzer.data['rentabilite_brute'].idxmax()]
        best_cashflow = analyzer.data.loc[analyzer.data['cash_flow_mensuel'].idxmax()]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🏆 Meilleur Score Global",
                value=f"{best_overall['ville']}",
                delta=f"{best_overall['score_rentabilite']:.1f} points"
            )
            st.write(f"Rentabilité: {best_overall['rentabilite_brute']:.1f}%")
            st.write(f"Cash-flow: {best_overall['cash_flow_mensuel']:.0f}€/mois")
        
        with col2:
            st.metric(
                label="📈 Meilleure Rentabilité",
                value=f"{best_rentability['ville']}",
                delta=f"{best_rentability['rentabilite_brute']:.1f}%"
            )
            st.write(f"Prix: {best_rentability['prix_achat_m2']:,.0f}€/m²")
            st.write(f"Loyer: {best_rentability['loyer_m2_mois']:.0f}€/m²/mois")
        
        with col3:
            st.metric(
                label="💰 Meilleur Cash-flow",
                value=f"{best_cashflow['ville']}",
                delta=f"{best_cashflow['cash_flow_mensuel']:.0f}€/mois"
            )
            st.write(f"Rentabilité: {best_cashflow['rentabilite_brute']:.1f}%")
            st.write(f"Retour: {best_cashflow['temps_retour_annees']:.1f} ans")
        
        # Conseils généraux
        st.markdown("---")
        st.markdown("### 📋 Points Clés à Retenir")
        st.markdown("""
        - **Rentabilité brute** : Ratio loyer annuel / prix d'achat
        - **Cash-flow** : Différence entre loyer perçu et charges (emprunt, taxes, entretien)
        - **Score global** : Combinaison pondérée de tous les critères
        - Les données sont basées sur des moyennes et peuvent varier selon le quartier
        - Pensez à vérifier les tendances du marché local avant d'investir
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("*💡 Cette application utilise des données d'exemple. Pour un investissement réel, consultez des sources officielles et des professionnels.*")

if __name__ == "__main__":
    main()