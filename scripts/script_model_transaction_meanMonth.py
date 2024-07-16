import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import pickle
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Charger les données
logging.info("Chargement des données...")
engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")
query = "SELECT * FROM transactions WHERE date_transaction >= '2015-01-01'"
df = pd.read_sql(query, engine)
logging.info("Données chargées.")

# Agréger les prix par mois et par département
logging.info("Agrégation des données par mois et par département...")
df['date_transaction'] = pd.to_datetime(df['date_transaction'])
df['month'] = df['date_transaction'].dt.to_period('M')
grouped_df = df.groupby(['month', 'departement'])['prix'].mean().reset_index()
grouped_df['month'] = grouped_df['month'].astype(str)  # Convertir les périodes en chaînes de caractères

# Préparer les données
logging.info("Préparation des données...")
X = grouped_df[['month', 'departement']]
y = grouped_df['prix']

# Pipeline de prétraitement
numeric_features = ['departement']
categorical_features = ['month']

numeric_transformer = Pipeline(steps=[
    ('scaler', StandardScaler())])

categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)])

# Préparer le pipeline complet
pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                           ('regressor', LinearRegression())])

# Diviser les données en ensembles d'entraînement et de test
logging.info("Division des données en ensembles d'entraînement et de test...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraînement du modèle
logging.info("Entraînement du modèle de régression linéaire...")
pipeline.fit(X_train, y_train)
logging.info("Modèle entraîné.")

# Évaluer le modèle
logging.info("Évaluation du modèle...")
y_pred = pipeline.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
logging.info(f"Mean Squared Error: {mse}")

# Enregistrer le modèle et les colonnes
logging.info("Enregistrement du modèle et des colonnes...")
with open('models/model_transaction_meanMonth5.pkl', 'wb') as file:
    pickle.dump(pipeline, file)

with open('models/columns.pkl', 'wb') as file:
    pickle.dump(pipeline.named_steps['preprocessor'].get_feature_names_out(), file)

logging.info("Modèle entraîné et enregistré avec succès.")
