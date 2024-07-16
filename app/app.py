import os
from dotenv import load_dotenv
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import folium
import pickle
from dash.dependencies import Input, Output

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Obtenir les informations de configuration de la base de données depuis les variables d'environnement
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Connexion à la base de données MySQL
config = {
    'host': db_host,
    'user': db_user,
    'password': db_password,
    'database': db_name
}

engine = create_engine(f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}/{config['database']}")

# Charger les données
query = "SELECT date_transaction, prix, n_pieces, surface_habitable, latitude, longitude FROM transactions LIMIT 1000"
df = pd.read_sql(query, engine)

# Charger le modèle de prédiction
with open('model.pkl', 'rb') as file:
    model = pickle.load(file)

# Créer les prédictions pour les points de données
df['predicted_price'] = model.predict(df[['year', 'n_pieces', 'surface_habitable']])

# Créer l'application Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout de l'application
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Tableau de Bord ImmoDB"), className="mb-2")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(
            figure={
                'data': [
                    {'x': df['date_transaction'], 'y': df['prix'], 'type': 'bar', 'name': 'Prix des transactions'}
                ],
                'layout': {
                    'title': 'Prix des Transactions par Date'
                }
            }
        ), className="mb-4")
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='map'), className="mb-4")
    ])
])

@app.callback(
    Output('map', 'children'),
    [Input('map', 'id')]
)
def update_map(_):
    # Créer la carte
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=6)

    # Ajouter les points de données à la carte
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Prix prédit: {row['predicted_price']} EUR",
            tooltip=row['prix']
        ).add_to(m)

    # Enregistrer la carte dans un fichier HTML
    m.save('map.html')

    # Lire le contenu du fichier HTML et l'afficher
    with open('map.html', 'r', encoding='utf-8') as file:
        return file.read()

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
