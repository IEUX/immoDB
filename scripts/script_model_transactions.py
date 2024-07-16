import os
import time
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import pickle

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Charger les données
engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")
query = "SELECT * FROM transactions WHERE date_transaction >= '2020-01-01'"
df = pd.read_sql(query, engine)

print("Données chargées.")

# Préparer les données
df['date_transaction'] = pd.to_datetime(df['date_transaction']).map(pd.Timestamp.to_julian_date)
X = df[['date_transaction', 'departement', 'ville', 'type_batiment', 'vefa', 'n_pieces', 'surface_habitable', 'latitude', 'longitude']]
y = df['prix']

# Prétraitement des données
numeric_features = ['date_transaction', 'n_pieces', 'surface_habitable', 'latitude', 'longitude', 'departement']
categorical_features = ['type_batiment', 'vefa', 'ville']

numeric_transformer = Pipeline(steps=[
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Créer le pipeline de prétraitement et de modèle
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor())
])

# Diviser les données en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("Données divisées en ensembles d'entraînement et de test.")

# Définir les hyperparamètres pour la recherche en grille
param_grid = {
    'regressor__n_estimators': [100, 200, 300],
    'regressor__max_features': [1.0, 'sqrt', 'log2'],
    'regressor__max_depth': [10, 20, 30, None]
}

grid_search = GridSearchCV(estimator=model, param_grid=param_grid, cv=5, scoring='neg_mean_squared_error')
print("Début de la recherche en grille des hyperparamètres...")
grid_search.fit(X_train, y_train)

# Évaluer le modèle
best_model = grid_search.best_estimator_
y_pred = best_model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse}")

# Enregistrer le modèle
with open('model.pkl', 'wb') as file:
    pickle.dump(best_model, file)

print("Modèle enregistré sous 'model.pkl'.")
