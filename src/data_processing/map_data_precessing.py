import requests
import pandas as pd

def API_get_coordinates(query: str) -> tuple:
    ADDOK_URL = 'http://api-adresse.data.gouv.fr/search/'
    params = {
        'q': query,
        'limit': 5
    }
    try:
        response = requests.get(ADDOK_URL, params=params)
        j = response.json()
        if len(j.get('features')) > 0:
                first_result = j.get('features')[0]
                lon, lat = first_result.get('geometry').get('coordinates')
                # first_result_all_infos = { **first_result.get('properties'), **{"lon": lon, "lat": lat}}
                print(f"{query} : {lon}, {lat}")
        else:
            lon, lat = None, None
            print('No result')
    except:
        lon, lat = None, None
    return lon, lat

def geocode_df(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Géocode le dataframe joint des DVF et des loyers à partir du code commune INSEE
    et du libellé de commune.
    """
    comm_df = merged_df[['INSEE_C', 'LIBGEO']].drop_duplicates()

    for idx, row in comm_df.iterrows():
        query = str(row.INSEE_C) + str(row.LIBGEO)
        lon, lat = API_get_coordinates(query)

        comm_df.at[idx, 'lon'] = lon
        comm_df.at[idx, 'lat'] = lat

    return comm_df