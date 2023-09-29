import json
import os
from datetime import datetime

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import math
from dash import dcc, html
from dash.dependencies import Input, Output, State

# Chargez vos données CSV
cwd = os.getcwd()
chemin=os.path.join(cwd, "output")
csv_files = [f for f in os.listdir(chemin) if f.startswith('out_all_2023-09-')]

map_resources=os.path.join(cwd, "resources", "departements.geojson")

dfs = []

for csv in csv_files:
    df = pd.read_csv(os.path.join(chemin, csv))
    dfs.append(df)
df = pd.concat(dfs, ignore_index=True)
df = df.dropna(axis=0)
print(datetime.now())

# Chargez les données géospatiales pour les départements de la France au format GeoJSON
with open(map_resources, 'r') as geojson_file:
    france_geojson = json.load(geojson_file)
    

app = dash.Dash(__name__)

# Créez une liste triée des options pour le Dropdown à partir de la colonne 'dep'
dep_options = sorted([{'label': dep, 'value': dep} for dep in df['dep'].unique()], key=lambda x: x['label'])

# Créez une liste triée des options pour le Checklist à partir de la colonne 'species_name'
species_name_options =  sorted([{'label': species_name, 'value': species_name} for species_name in df['species_name'].unique()], key=lambda x: x['label'])
species_name_top = df.groupby(['species_name'])['birds_count'].sum().sort_values(ascending=False).head(10)

app.layout = html.Div([
    html.Div([
        dcc.RangeSlider(
            id='date-range-slider',
            marks={i: {'label': date} for i, date in enumerate(sorted(df['date'].unique()))},
            min=0,
            max=len(df['date'].unique()) - 1,
            step=1,
            value=[0, len(df['date'].unique()) - 1],  # Plage temporelle complète par défaut
        ),
        dcc.Dropdown(
            id='dep-dropdown',
            options=dep_options,
            multi=True,
            value=list(df['dep'].unique()),  # Tous les départements sélectionnés par défaut
            placeholder="Sélectionnez les départements",
        ),
        html.Button("Sélectionner toutes les espèces", id="select-all"),
        dcc.Store(id='select-all-state', data=0),
        dcc.Dropdown(
            id='species-name-dropdown',
            options=species_name_options,
            multi=False,
            placeholder="Sélectionnez les espèces",
        )
        ], style={'position': 'sticky', 'left': 100,'top': 20, 'width': '60%', 'zIndex': 1000, 'background-color':'white', 'box-shadow': 'inset 2px 2px 10px rgba(255,255,255,.1), inset -5px -8px 8px rgba(0,0,0,.2)'}),
    html.Div([
        dcc.Graph(id='map-fig', style={'height': '80vh'}),  # Hauteur de la carte plus grande
        ], style={'position': 'float','margin-top': '15px'}),
    html.Div([
        dcc.Graph(id='graph-fig'),
        dcc.Graph(id='batton-fig'),
        dcc.Graph(id='pie-fig')
        ], style={'position': 'float','margin-top': '5px', 'width': '60%', 'margin-left': 'auto', 'margin-right': 'auto'})
])

@app.callback(
    [Output('map-fig', 'figure'),
     Output('pie-fig', 'figure'),
     Output('graph-fig', 'figure'),
     Output('batton-fig', 'figure')],
    [Input('dep-dropdown', 'value'),
     Input('species-name-dropdown', 'value'),
     Input('date-range-slider', 'value'),
     Input("select-all", "n_clicks")
    ],
    State('species-name-dropdown', 'options'),
    State('species-name-dropdown', 'value'),
    State('select-all-state', 'data') 
)
def update_map(selected_deps, selected_species, date_range, n_clicks, species_name_options, selected_species_values, select_all_state):
    print("****** ***** ****** *********** ********* ********* ********** *****")
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'select-all' in changed_id:
        # Si le bouton "Select All" a été cliqué, basculez l'état du Store
        select_all_state = (select_all_state + 1) % 2

    # Selection de toutes les espèces
    if select_all_state == 1:
        selected_species=list(df['species_name'].unique())
        selected_species_values = [species['value'] for species in species_name_options]
        
    start_date = sorted(df['date'].unique())[date_range[0]]
    end_date = sorted(df['date'].unique())[date_range[1]]

    # Filtre par départements et dates
    filtered_df = df[
        (df['dep'].isin(selected_deps)) & 
        (df['date'] >= start_date) & (df['date'] <= end_date)]
    filtered_df['birds_count'] = filtered_df['birds_count'].astype(int)
    # Top 10 des espèces par département/date
    species_name_top=filtered_df.groupby(['species_name'])['birds_count'].sum().sort_values(ascending=False).head(10)

    # Filtre des espèces lorsqu'on en sélectionne une
    if select_all_state != 1 and selected_species is not None :
        filtered_df = filtered_df[filtered_df.species_name == selected_species_values]

    # Créer une échelle de couleur personnalisée pour 'birds_count'
    marker_colorscale = [
        [0, 'green'],  # Couleur verte pour les valeurs faibles
        [0.05, 'blue'],
        [1, 'red']  # Couleur rouge pour les valeurs élevées
    ]

    # Calculer la taille des points en fonction de 'birds_count'
    min_marker_size = 10
    max_marker_size = 100
    print(filtered_df['birds_count'].min())
    print(filtered_df['birds_count'].max())
    marker_size_range = (filtered_df['birds_count'].min(), filtered_df['birds_count'].max())
    filtered_df['marker_size'] = filtered_df['birds_count'].apply(
        lambda x: min_marker_size + (max_marker_size - min_marker_size) * (math.exp2(math.log(x+1))*5 - marker_size_range[0]) / (marker_size_range[1] - marker_size_range[0])
    )
    print(filtered_df)

    # Créer une carte de contours des départements de la France
    map_fig = go.Figure(go.Choroplethmapbox(
        geojson=france_geojson,
        locations=filtered_df['dep'],
        z=filtered_df['birds_count'],
        hovertext=filtered_df.apply(lambda row: f"{row['species_name']} ({row['birds_count']})", axis=1),
        hovertemplate='%{hovertext}<extra></extra>',
        colorscale=marker_colorscale,
        showscale=True,
        marker_line_width=0,
        marker_opacity=0.7,
    ))

    # Ajouter les points géolocalisés à la carte
    map_fig.add_trace(go.Scattermapbox(
        lat=filtered_df['lat'],
        lon=filtered_df['lon'],
        mode='markers',
        marker=dict(
            size=filtered_df['marker_size'],
            opacity=0.7,
            colorscale=marker_colorscale,
            cmin=filtered_df['birds_count'].min(),
            cmax=filtered_df['birds_count'].max(),
            color=filtered_df['birds_count'],
        ),
        text=filtered_df.apply(lambda row: f"{row['species_name']} ({row['birds_count']})", axis=1),
        hoverinfo='text',
    ))

    # Personnalisez la mise en page de la carte
    map_fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=6,
        mapbox_center={"lat": 49.103354, "lon": 0},
    )

    # Créer un graphique camembert pour la répartition des espèces
    pie_fig = go.Figure(go.Pie(
        labels=species_name_top.index,
        values=species_name_top.values,
        textinfo='label+percent',
        hoverinfo='label+value',
    ))
    pie_fig.update_layout(title=f'Les 10 espèces les plus comptées pour la période de {start_date} à {end_date}')

    # Grouper les données par jour et calculer la somme des espèces pour chaque jour
    species_count_by_day = filtered_df.groupby('date')['birds_count'].sum()

    # Créer un graphique de ligne pour la somme des espèces en fonction du jour
    graph_figure = {
        'data': [
            {
                'x': species_count_by_day.index,
                'y': species_count_by_day.values,
                'type': 'line',
                'mode': 'lines+markers',
                'name': 'Somme des espèces',
            }
        ],
        'layout': {
            'title': 'Somme totale de ou des espèces par jour',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Somme des espèces'},
            'step': 1,
        }
    }

    # Grouper les données par département et calculer la somme des espèces pour chaque département
    species_count_by_department = filtered_df.groupby('dep')['birds_count'].sum()
    # Créer un graphique en baton
    batton_figure = {
        'data': [
            {
                'x': species_count_by_department.index,
                'y': species_count_by_department.values,
                'type': 'bar',
                'name': 'Somme des espèces par département',
            }
        ],
        'layout': {
            'title': 'Somme des espèces par département',
            'xaxis': {'title': 'Département', 'type': 'category'},
            'yaxis': {'title': 'Somme des espèces'},
        }
    }

    return map_fig, pie_fig, graph_figure, batton_figure

# Méthode pour reset l'espece sélectionnée quand on clique sur le bouton 'Selectionner toutes les espèces
@app.callback(
    Output('species-name-dropdown', 'value'),
    Input("select-all", "n_clicks"))
def reset_species(n_clicks):
    return None


if __name__ == '__main__':
    app.run_server(debug=True)