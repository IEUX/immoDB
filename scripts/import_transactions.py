import time
import os
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Définir la connexion MySQL en utilisant SQLAlchemy
db_url = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = sqlalchemy.create_engine(db_url)
Session = sessionmaker(bind=engine)

_start = time.time()


def log_in_out(func):
    # Décorateur pour enregistrer les appels de fonction
    def decorated_func(*args, **kwargs):
        start = time.time()
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))} - [INIT]: Enter {func.__name__}")
        result = func(*args, **kwargs)
        end = time.time()
        print(
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))} - [INIT]: {func.__name__} done in {round(end - start)}s")
        return result

    return decorated_func


@log_in_out
def read_transactions(file):
    # Ouvrir le fichier de transactions et le convertir en DataFrame
    arrays = dict(np.load(file))
    data = {k: [s.decode("utf-8") for s in v.tobytes().split(b"\x00")] if v.dtype == np.uint8 else v for k, v in
            arrays.items()}
    df_trans = pd.DataFrame.from_dict(data)
    return df_trans


@log_in_out
def clean_transactions(df_transactions):
    # Afficher les colonnes avant le nettoyage
    print("Colonnes avant le nettoyage: ", df_transactions.columns.tolist())

    # Supprimer les colonnes inutiles
    columns_to_drop = ['id_transaction', 'id_ville', 'code_postal', 'adresse', 'id_parcelle_cadastre',
                       'surface_dependances', 'surface_locaux_industriels', 'surface_terrains_agricoles',
                       'surface_terrains_sols', 'surface_terrains_nature']
    df_transactions = df_transactions.drop(columns=[col for col in columns_to_drop if col in df_transactions.columns])

    # Afficher les colonnes après la suppression des colonnes inutiles
    print("Colonnes après suppression des colonnes inutiles: ", df_transactions.columns.tolist())

    initial_len = len(df_transactions)
    df_transactions = clean_transactions_absurd(df_transactions)

    # Vérifier les colonnes après le nettoyage des valeurs absurdes
    print("Colonnes après clean_transactions_absurd: ", df_transactions.columns.tolist())

    print(
        f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} - [INIT]: {initial_len - len(df_transactions)} row suppressed! That represents {((initial_len - len(df_transactions)) / len(df_transactions)) * 100:.2f}% of data")
    return df_transactions


@log_in_out
def clean_transactions_absurd(df_trans):
    # Calculer les statistiques moyennes
    grouped_stats = df_trans.groupby([pd.to_datetime(df_trans['date_transaction']).dt.year, 'departement'])[
        ['prix', 'surface_habitable']].apply(
        lambda x: (x['prix'] / x['surface_habitable']).agg(['median', 'std'])).reset_index(drop=False)
    # Créer une colonne year pour joindre `grouped_stats` et le DataFrame initial
    df_trans['year'] = pd.to_datetime(df_trans['date_transaction']).dt.year
    # Fusionner `grouped_stats` et le DataFrame initial
    to_clean_df = pd.merge(df_trans, grouped_stats, left_on=['year', 'departement'],
                           right_on=['date_transaction', 'departement'], suffixes=('', '_stats'))
    # Supprimer les valeurs absurdes où le prix/m² est 3 fois plus que l'écart type
    filtered_df = to_clean_df[
        (to_clean_df['prix'] / to_clean_df['surface_habitable']) < to_clean_df['median'] + 3 * to_clean_df['std']]
    # Supprimer les colonnes temporaires
    filtered_df = filtered_df.drop(columns=['median', 'std', 'year', 'date_transaction_stats'])
    return filtered_df


@log_in_out
def write_to_db(dataframe, table, chunksize=10000):
    session = Session()
    try:
        for i in range(0, len(dataframe), chunksize):
            chunk = dataframe.iloc[i:i + chunksize]
            chunk.to_sql(name=table, con=engine, if_exists='append', index=False)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


# Chemin du fichier transactions
transactions_file = os.getenv('SOURCES_TRANSACTIONS')
df = read_transactions(transactions_file)
df = clean_transactions(df)
write_to_db(df, "transactions")

print(
    f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} - [END INIT]: Data Import done in {round(time.time() - _start)}")
