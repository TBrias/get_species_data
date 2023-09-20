import requests
import pandas as pd
from datetime import datetime

data_list = []
page = 1
# Indice du département (1 = prise en compte du dep à la position cible)
#deps = '000000000000000000000000000000000000000000000000000000000000000000000000111110000000000000000000000000'
deps = '11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111100000'

start_time = datetime.now()
today = datetime.now().strftime("%Y-%m-%d")

print(f"Lancement du script: {start_time}")

# On boucle sur les pages
while page < 1000:
    url = f'https://www.MY_WEBSITE.org/index.php?m_id=1351&content=observations_by_page&backlink=skip&p_c=duration&p_cc=-&sp_tg=1&sp_DateSynth=19.09.2023&sp_DChoice=offset&sp_DOffset=2&sp_SChoice=category&sp_Cat[never]=1&sp_Cat[veryrare]=1&sp_Cat[rare]=1&sp_Cat[unusual]=1&sp_Cat[escaped]=1&sp_Cat[common]=1&sp_Cat[verycommon]=1&sp_PChoice=canton&sp_cC={deps}&sp_FChoice=list&sp_FGraphFormat=auto&sp_FMapFormat=none&sp_FDisplay=DATE_PLACE_SPECIES&sp_FOrder=ALPHA&sp_FOrderListSpecies=ALPHA&sp_FListSpeciesChoice=DATA&sp_FOrderSynth=ALPHA&sp_FGraphChoice=DATA&sp_DFormat=DESC&sp_FAltScale=250&sp_FAltChoice=DATA&sp_FExportFormat=XLS&mp_current_page={page}&txid={page}'
    html = requests.get(url)
    j = html.json()
    df = pd.DataFrame.from_dict(j)

    # Si pas de données sur la page, on arrête
    if df.data_is_finished.empty:
        print ("Il n'y a pas d'autre page pour ce jour")
        break

    # Lecture de chaque ligne de résultat
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

    page += 1

mid_time = datetime.now()
print(f"Fin des requête de récupération: {mid_time}")
print(f"Nombre de page récupérée: {page}")

if not data_list:
    print("Aucune donnée n'a été récupérée")
else:
    df_final = pd.DataFrame(data_list)

    # On enlève les greater/lower dans birds_count
    df_final.birds_count = df_final.birds_count.apply(lambda x: x.split(';')[-1] if ';' in x else x)
    df_final.birds_count = df_final.birds_count.apply(lambda x: x.split('~')[-1] if '~' in x else x)

    print(df_final)

    df_final.to_csv(f"out_{today}.csv", index=False)

    
diff_time = datetime.now() - start_time
print(f"Fin du script: {datetime.now()}")
print(f"Durée du script: {diff_time}")
