import pandas as pd
import streamlit as st
from math import radians, cos, sin, sqrt, atan2

from src.data.data_dl_url import COMMUNE_GEOCODED_URL



def is_within_radius(center_lat, center_lon, radius_km, point_lat, point_lon):
    """
    Vérifie si un point (point_lat, point_lon) se trouve dans un rayon donné (radius_km)
    autour d'un point central (center_lat, center_lon).
    """
    R = 6371.0  # Rayon approximatif de la Terre en km
    # Conversion des degrés en radians
    lat1_rad = radians(center_lat)
    lon1_rad = radians(center_lon)
    lat2_rad = radians(point_lat)
    lon2_rad = radians(point_lon)
    # Différence entre les longitudes et latitudes
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    # Formule de Haversine
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance <= radius_km

def geocode_df(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Géocode le dataframe joint des DVF et des loyers à partir du code commune INSEE
    et du libellé de commune.
    """
    max_year = merged_df['annee'].max()
    comm_df = merged_df[merged_df['annee'] == max_year][['INSEE_C', 'LIBGEO', 'loypredm2', 'prof_rate']].drop_duplicates()
    geocoded_df = pd.read_csv(COMMUNE_GEOCODED_URL['2025'], encoding='utf-8', sep=',', decimal='.')
    geocoded_comm_df = comm_df.merge(geocoded_df[['code_commune_insee', 'latitude', 'longitude']],
                                     left_on='INSEE_C',
                                     right_on='code_commune_insee',
                                     how='left')
    geocoded_comm_df['prof_rate'] = geocoded_comm_df['prof_rate'].astype('float64')

    return geocoded_comm_df

def calculate_prof_rate_color(prof_rate: float) -> str:
    """
    Retourne une couleur en fonction du taux de profitabilité.
    """
    if prof_rate < 4.0:
        return '#ff0000'
    elif prof_rate < 7.0:
        return '#e3ba54'
    else:
        return '#32a852'
    
@st.cache_data
def get_geocoded_data(merged_df: pd.DataFrame) -> pd.DataFrame:
    # Géocoder les données mergées
    geocoded_df = geocode_df(merged_df)
    # Supprimer les lignes sans coordonnées géographiques
    geocoded_df = geocoded_df.dropna(subset=['latitude', 'longitude'])
    # Ajouter une colonne de couleur en fonction du taux de profitabilité
    geocoded_df['prof_rate_color'] = geocoded_df['prof_rate'].apply(calculate_prof_rate_color)
    return geocoded_df