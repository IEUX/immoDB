import os
import time
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Assign variables from environment
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
transactions_file = os.getenv('SOURCES_TRANSACTIONS')

# Ensure transactions_file is correctly set
if transactions_file is None:
    raise ValueError("The environment variable 'SOURCES_TRANSACTIONS' is not set. Please check your .env file.")

db_url = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

_start = time.time()

def log_in_out(func):
    def decorated_func(*args, **kwargs):
        start = time.time()
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))} - [INIT]: Enter {func.__name__}")
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))} - [INIT]: {func.__name__} done in {round(end - start)}s")
        return result
    return decorated_func

@log_in_out
def read_transactions(file):
    arrays = dict(np.load(file))
    data = {k: [s.decode("utf-8") for s in v.tobytes().split(b"\x00")] if v.dtype == np.uint8 else v for k, v in arrays.items()}
    df_trans = pd.DataFrame.from_dict(data)
    return df_trans

@log_in_out
def clean_transactions(df_transactions):
    initial_len = len(df_transactions)
    clean_df = clean_transactions_absurd(df_transactions)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} - [INIT]: {initial_len - len(clean_df)} row suppressed ! That represents {((initial_len - len(clean_df)) / len(clean_df)) * 100:.2f}% of data")
    return clean_df

@log_in_out
def clean_transactions_range(df_trans):
    df_trans.drop(df_trans[df_trans['prix'] < int(os.getenv('MIN_PRICE'))].index, inplace=True)
    return df_trans

@log_in_out
def clean_transactions_absurd(df_trans):
    grouped_stats = df_trans.groupby([pd.to_datetime(df_trans['date_transaction']).dt.year, 'departement'])[['prix', 'surface_habitable']].apply(
        lambda x: (x['prix'] / x['surface_habitable']).agg(['median', 'std'])).reset_index(drop=False)
    df_trans['year'] = pd.to_datetime(df_trans['date_transaction']).dt.year
    to_clean_df = pd.merge(df_trans, grouped_stats, left_on=['year', 'departement'],
                           right_on=['date_transaction', 'departement'], suffixes=('', '_stats'))
    filtered_df = to_clean_df[((to_clean_df['prix'] / to_clean_df['surface_habitable']) < to_clean_df['median'] + 2 * to_clean_df['std']) & ((to_clean_df['prix'] / to_clean_df['surface_habitable']) > to_clean_df['median'] - 2 * to_clean_df['std'])]
    filtered_df = filtered_df.drop(columns=['median', 'std', 'year'])
    return filtered_df

@log_in_out
def write_to_db(dataframe, table, chunksize=10000):
    session = Session()
    try:
        for i in range(0, len(dataframe), chunksize):
            chunk = dataframe.iloc[i:i+chunksize]
            chunk.to_sql(name=table, con=engine, if_exists='append', index=False)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

df = read_transactions(transactions_file)
df = clean_transactions(df)
write_to_db(df, "transactions")

print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} - [END INIT]: Data Import done in {round(time.time() - _start)}s")
