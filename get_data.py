import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import dateparser
import pandas as pd
import requests

start_time = datetime.now()
today = datetime.now().strftime("%Y-%m-%d")
page = 1
# Indice du département (1 = prise en compte du dep à la position cible)
deps =  '00000000000001000000000001000000000000000000000000100000000001000000000000001000000000000000000000000'
#deps =  '00000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000'
#deps = '11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111100000'

print(f"Lancement du script: {start_time}")

def fetch_data(page):
    try:
        url = f'https://www.faune-normandie.org/index.php?m_id=1351&content=observations_by_page&backlink=skip&p_c=duration&p_cc=-&sp_tg=1&sp_DateSynth=19.09.2023&sp_DChoice=offset&sp_DOffset=15&sp_SChoice=category&sp_Cat[never]=1&sp_Cat[veryrare]=1&sp_Cat[rare]=1&sp_Cat[unusual]=1&sp_Cat[escaped]=1&sp_Cat[common]=1&sp_Cat[verycommon]=1&sp_PChoice=canton&sp_cC={deps}&sp_FChoice=list&sp_FGraphFormat=auto&sp_FMapFormat=none&sp_FDisplay=DATE_PLACE_SPECIES&sp_FOrder=ALPHA&sp_FOrderListSpecies=ALPHA&sp_FListSpeciesChoice=DATA&sp_FOrderSynth=ALPHA&sp_FGraphChoice=DATA&sp_DFormat=DESC&sp_FAltScale=250&sp_FAltChoice=DATA&sp_FExportFormat=XLS&mp_current_page={page}&txid={page}'
        html = requests.get(url)
        j = html.json()
        df = pd.DataFrame.from_dict(j)

        if page % 10 == 0:
            print(f"Page en cours: {page} au timing: {datetime.now()}, encore des données: {not df.data_is_finished.empty}")

        if not df.data_is_finished.empty:
            for row in df.data:
                data = {
                    'birds_count': row['birds_count'],
                    'species_id': row['species_array']['id'],
                    'species_name': row['species_array']['name'],
                    'species_latin_name': row['species_array']['latin_name'],
                    'species_rarity': row['species_array']['rarity'],
                    'lat': row['lat'],
                    'lon': row['lon'],
                    'area': row['listSubmenu']['title'],
                    'date': row['listTop']['title']
                }
                data_list.append(data)
            return True
        else:
            print(f"Plus de données disponibles pour la page: {page}")
            return False
    except Exception as e:
        print(f"Error fetching data for page {page}: {str(e)}")
    return False

data_list = []
page = 1
total_pages = 200

while page <= total_pages and fetch_data(page):
    page+=1

mid_time = datetime.now()
print(f"Fin des requêtes de récupération: {mid_time}")
print(f"Nombre de page récupérée: {page}")

if not data_list:
    print("Aucune donnée n'a été récupérée")
else:
    df_final = pd.DataFrame(data_list)

    # On enlève les greater/lower dans birds_count
    df_final.birds_count = df_final.birds_count.apply(lambda x: x.split(';')[-1] if ';' in x else x)
    df_final.birds_count = df_final.birds_count.apply(lambda x: x.split('~')[-1] if '~' in x else x)
    df_final.birds_count = df_final.birds_count.apply(lambda x: x.split('-')[0] if '-' in x else x)

    # On enlève les zéro + les champs vides
    df_final = df_final[(df_final.birds_count != 0) & (df_final.birds_count != '0')]
    df_final = df_final[pd.to_numeric(df_final.birds_count, errors='coerce').notna()]
    df_final = df_final.dropna(how='any', axis=0)

    # Extraction du département:
    df_final['dep'] = df_final['area'].str.extract(r'\((\d+)\)')
    occurrences = df_final['dep'].value_counts().sort_values()

    # Changement de format pour la date
    df_final['date'] = df_final['date'].apply(lambda x: dateparser.parse(x).strftime('%Y-%m-%d'))

    print(df_final)

    cwd = os.getcwd()
    df_final.to_csv(os.path.join(cwd, "output", f"out_all_{today}_normandie.csv"), index=False)


    
diff_time = datetime.now() - start_time
print(f"Fin du script: {datetime.now()}")
print(f"Durée du script: {diff_time}")
