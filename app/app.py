import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
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

# Charger un échantillon des données (assurez-vous que la table 'transactions' existe dans votre base de données)
query = "SELECT date, prix FROM transactions LIMIT 1000"
df = pd.read_sql(query, engine)

# Créer l'application Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout de l'application
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Tableau de Bord ImmoDB"), className="mb-2")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='transactions-graph'), className="mb-4")
    ]),
    dbc.Row([
        dbc.Col(dcc.Slider(
            id='data-slider',
            min=1000,
            max=10000,
            step=1000,
            value=1000,
            marks={i: str(i) for i in range(1000, 10001, 1000)}
        ), width=12)
    ])
])

@app.callback(
    Output('transactions-graph', 'figure'),
    [Input('data-slider', 'value')]
)
def update_graph(rows):
    query = f"SELECT date, prix FROM transactions LIMIT {rows}"
    df = pd.read_sql(query, engine)
    figure = {
        'data': [
            {'x': df['date'], 'y': df['prix'], 'type': 'bar', 'name': 'Prix des transactions'}
        ],
        'layout': {
            'title': 'Prix des Transactions par Date'
        }
    }
    return figure

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
