import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
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
query = """
SELECT 
    DATE_FORMAT(date_transaction, '%Y-%m') AS month,
    departement,
    AVG(prix) AS prix_moyen
FROM transactions
GROUP BY month, departement
"""
df = pd.read_sql(query, engine)
logging.info("Données chargées.")

# Préparer les données
logging.info("Préparation des données...")
df['month'] = pd.to_datetime(df['month'])
df['departement'] = df['departement'].astype(int)
df['year'] = df['month'].dt.year
df['month_num'] = df['month'].dt.month
df['month'] = df['month'].dt.to_period('M').astype(str)

# Générer les prédictions pour chaque département
future_dates = pd.date_range(start='2024-01', periods=24, freq='M')
future_months = future_dates.to_period('M').astype(str)
departements = df['departement'].unique()
all_predictions = []

for dept in departements:
    logging.info(f"Traitement du département {dept}...")
    df_dept = df[df['departement'] == dept]

    if len(df_dept) < 2:
        logging.warning(f"Pas assez de données pour le département {dept}, ignoré.")
        continue

    X = df_dept[['year', 'month_num']]
    y = df_dept['prix_moyen']

    # Pipeline de prétraitement
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['year', 'month_num'])])

    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                               ('regressor', LinearRegression())])

    # Diviser les données en ensembles d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraînement du modèle
    pipeline.fit(X_train, y_train)

    # Évaluation du modèle
    train_score = pipeline.score(X_train, y_train)
    test_score = pipeline.score(X_test, y_test)
    mse = mean_squared_error(y_test, pipeline.predict(X_test))

    logging.info(
        f"Département {dept} - Train Score: {train_score}, Test Score: {test_score}, Mean Squared Error: {mse}")

    # Préparation des données futures pour les prédictions
    future_data = pd.DataFrame({
        'month': future_months,
        'year': future_dates.year,
        'month_num': future_dates.month,
        'departement': dept
    })

    # Faire les prédictions
    future_predictions = pipeline.predict(future_data[['year', 'month_num']])
    future_data['prix_moyen'] = future_predictions

    # Ajouter les prédictions au dataframe
    all_predictions.append(future_data)

# Combiner les prédictions avec les données historiques
combined_df = pd.concat([df] + all_predictions, ignore_index=True)

# Sauvegarder les données combinées dans un fichier CSV
logging.info("Sauvegarde des données combinées dans un fichier CSV...")
combined_df.to_csv('historical_and_predictions_monthly.csv', index=False)
logging.info("Données combinées sauvegardées avec succès dans 'historical_and_predictions_monthly.csv'.")

# Afficher les scores du modèle pour le dernier département traité
print(f"Train Score: {train_score}")
print(f"Test Score: {test_score}")
print(f"Mean Squared Error: {mse}")
