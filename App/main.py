import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, callback, Output, Input
import json
import flask



# Load data
df = pd.read_csv(f"data/dataset.csv", sep=',', dtype={"departement": str})

# Load GeoJSON 
zipcodes = json.load(open("data/departements.geojson"))

# Create flask server
server = flask.Flask(__name__)

# Dash App Init
app = Dash(__name__,  server=server)
app.layout = [
        html.Div(className='content', children=[
                html.Div(className='header',
                        children=[
                        html.H1(children='immoDB', style={'font':'Roboto'})
                        ]),
                html.Div(className='featured',
                         children=[
                                html.Div(className='card', children=[
                                        html.H3(children='Découvrez notre carte des prix'),
                                        html.Img(src='assets/images/map.png', alt='map', style={'width':'90%', 'height': '75%', 'border-radius':'10px'}),
                                        html.A(html.Button('Voir la carte', className='btn', style={'font':'Roboto'}), href='#map')
                                ], style={'font':'Roboto'}),
                                html.Div(className='card', children=[
                                     html.H3(children='Suivez l\'évolution des prix', id='line'),
                                     html.Img(src='assets/images/line-chart.png', alt='map', style={'width':'90%','height': '75%', 'border-radius':'10px'}),
                                        html.A(html.Button('Voir l\'evolution', className='btn', style={'font':'Roboto'}), href='#line')
                                ], style={'font':'Roboto'}),
                                html.Div(className='card', children=[
                                     html.H3(children='Voir nos prévisions'),
                                ], style={'font':'Roboto'}),
                        ]),
                html.Div(className='graph-box', 
                        children=[
                                html.H2(children='Prix moyen du m² par département et par année', id='map'),
                                dcc.Dropdown(df.year.unique(), 2014, id='dropdown-map', className='map-selector'),
                                dcc.Graph(id='graph-content', className='map')
                                ]),
                html.Div(className='graph-box', 
                        children=[
                                html.H2(children='Evolutions des prix du m² par département'),
                                dcc.Dropdown(df.departement.unique(), "01", id='line-selection', className='map-selector'),
                                dcc.Graph(id='line-graph', className='map')
                                ])
        ])
                
        ]

# Update map by filtering the dataframe by year
@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-map', 'value')
)
def update_map(value):
    df_by_year = df[df.year==value]
    return px.choropleth_mapbox(df_by_year, geojson=zipcodes, locations='departement', color='prix_m2',
                           featureidkey="properties.code",
                           color_continuous_scale="Viridis",
                           range_color=(0, df['prix_m2'].max()),
                           mapbox_style="carto-positron",
                           zoom=5, center = {"lat": 46.40338, "lon": 2.17403},
                           opacity=0.5,
                           labels={'prix_m2':'Prix moyen du m²'}
                          )

# Update line graph by filtering the dataframe by departement
@callback(
    Output('line-graph', 'figure'),
    Input('line-selection', 'value')
)
def update_lineGraph(value):
    df_by_departement = df[df.departement==value]
    return px.line(df_by_departement, x='year', y='prix_m2')

if __name__ == '__main__':
    app.run(debug=True)
