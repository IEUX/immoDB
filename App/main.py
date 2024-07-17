import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, callback, Output, Input
import json
import flask
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import dash_bootstrap_components as dbc

# Load environment variables
load_dotenv()

# Database connection
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")

# Load data from the database
df = pd.read_sql("""
SELECT 
    YEAR(date_transaction) AS year,
    departement,
    AVG(prix) AS prix_moyen,
    type_batiment
FROM transactions
GROUP BY year, departement, type_batiment
""", engine)

df_loyers = pd.read_sql("""
SELECT 
    date AS year, 
    departement, 
    AVG(loyer_m2_appartement) AS loyer_m2_appartement, 
    AVG(loyer_m2_maison) AS loyer_m2_maison 
FROM loyers
GROUP BY year, departement
""", engine)

df_prevision = pd.read_sql("""
SELECT * FROM
  `immodb`.`prix_mensuel`
                           """, engine)
df_prevision['month'] = pd.to_datetime(df_prevision['month'], format='%Y-%m')

# Load GeoJSON
zipcodes = json.load(open("./data/departements.geojson"))

# Create flask server
server = flask.Flask(__name__)

# Dash App Init
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div(className='content', children=[
    html.Div(className='header', children=[
        html.H1(children='immoDB', style={'font': 'Roboto'})
    ]),
    html.Div(className='featured', children=[
        html.Div(className='card', children=[
            html.H3(children='Découvrez notre carte des prix'),
            html.Img(src='assets/images/map.png', alt='map', style={'width': '90%', 'height': '75%', 'border-radius': '10px'}),
            html.A(html.Button('Voir la carte', className='btn', style={'font': 'Roboto'}), href='#map')
        ], style={'font': 'Roboto'}),
        html.Div(className='card', children=[
            html.H3(children='Suivez l\'évolution des prix', id='line'),
            html.Img(src='assets/images/line-chart.png', alt='map', style={'width': '90%', 'height': '75%', 'border-radius': '10px'}),
            html.A(html.Button('Voir l\'evolution', className='btn', style={'font': 'Roboto'}), href='#line')
        ], style={'font': 'Roboto'}),
        html.Div(className='card', children=[
            html.H3(children='Voir nos prévisions'),
            html.Img(src='assets/images/previsions.png', alt='map', style={'width': '90%', 'height': '75%', 'border-radius': '10px'}),
            html.A(html.Button('Voir nos prévsions', className='btn', style={'font': 'Roboto'}), href='#prevision')
        ], style={'font': 'Roboto'})
    ]),
    html.Div(className='graph-box', children=[
        html.H2(children='Prix moyen du m² par département et par année', id='map'),
        dcc.Dropdown(df['year'].unique(), 2014, id='dropdown-map', className='map-selector'),
        dcc.Graph(id='graph-content', className='map')
    ]),
    html.Div(className='graph-box', children=[
        html.H2(children='Évolution des prix par département'),
        dcc.Dropdown(df['departement'].unique(), "01", id='line-selection', className='map-selector'),
        dcc.Graph(id='line-graph', className='map')
    ]),
    html.Div(className='graph-box', children=[
        html.H2(children='Répartition des types de bâtiments par département'),
        dcc.Dropdown(df['departement'].unique(), "01", id='pie-selection', className='map-selector'),
        dcc.Graph(id='pie-chart', className='map')
    ]),
    html.Div(className='graph-box', children=[
        html.H2(children='Prevision du prix des transactions par departement', id='prevision'),
        dcc.Dropdown(df_prevision['departement'].unique(), 1, id='prevision-selection', className='map-selector'),
        dcc.Graph(id='prevision-chart', className='map')
    ]),

    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Update map by filtering the dataframe by year
@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-map', 'value')
)
def update_map(value):
    df_by_year = df[df.year == value]
    return px.choropleth_mapbox(df_by_year, geojson=zipcodes, locations='departement', color='prix_moyen',
                                featureidkey="properties.code",
                                color_continuous_scale="Viridis",
                                range_color=(0, df['prix_moyen'].max()),
                                mapbox_style="carto-positron",
                                zoom=5, center={"lat": 46.40338, "lon": 2.17403},
                                opacity=0.5,
                                labels={'prix_moyen': 'Prix moyen des transactions'}
                                )

# Update line graph by filtering the dataframe by departement
@callback(
    Output('line-graph', 'figure'),
    Input('line-selection', 'value')
)
def update_lineGraph(value):
    df_by_departement = df[df.departement == value]
    return px.line(df_by_departement, x='year', y='prix_moyen', color='type_batiment')

# Update pie chart by filtering the dataframe by departement
@callback(
    Output('pie-chart', 'figure'),
    Input('pie-selection', 'value')
)
def update_pieChart(value):
    df_by_departement = df[df.departement == value]
    return px.pie(df_by_departement, names='type_batiment', values='prix_moyen')


@app.callback(
    Output('prevision-chart', 'figure'),
    Input('prevision-selection', 'value')
)
def update_chart(selected_departement):
    filtered_df = df_prevision[df_prevision['departement'] == selected_departement]
    fig = px.line(filtered_df, x='month', y='prix_moyen',
                  title=f'Prix Moyens Mensuels pour le Département {selected_departement}')
    return fig

# Display notebook page
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/notebook':
        with open('notebooks/carto.ipynb', 'r') as f:
            notebook_html = f.read()
        return html.Div([
            html.H2("Notebook Carto"),
            html.Iframe(srcDoc=notebook_html, style={"width": "100%", "height": "1000px"})
        ])
    else:
        return html.Div()

if __name__ == '__main__':
    app.run(debug=True)
