import os
import pandas as pd
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import folium
import pickle
from dash.dependencies import Input, Output
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Obtenir les informations de configuration de la base de données depuis les variables d'environnement
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Connexion à la base de données MySQL
engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")

# Charger les données
query = "SELECT date_transaction, prix, departement FROM transactions WHERE date_transaction >= '2015-01-01'"
df = pd.read_sql(query, engine)

# Charger le modèle et les colonnes
with open('models/model_transaction_meanMonth5.pkl', 'rb') as file:
    model = pickle.load(file)

with open('models/columns.pkl', 'rb') as file:
    columns = pickle.load(file)

# Préparer les données pour la prédiction
df['date_transaction'] = pd.to_datetime(df['date_transaction'])
df['month'] = df['date_transaction'].dt.to_period('M').astype(str)
X_pred = df[['month', 'departement']]

print("Colonnes avant transformation:", X_pred.columns)
X_pred_transformed = model.named_steps['preprocessor'].transform(X_pred)
print("Colonnes après transformation:", X_pred_transformed.shape)

# Réindexer les données transformées
X_pred_transformed = pd.DataFrame(X_pred_transformed, columns=model.named_steps['preprocessor'].get_feature_names_out())
X_pred_transformed = X_pred_transformed.reindex(columns=columns, fill_value=0)

# Créer les prédictions pour les points de données
df['predicted_price'] = model.named_steps['regressor'].predict(X_pred_transformed)

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
