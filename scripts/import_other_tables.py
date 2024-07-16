import time
import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import configparser
import os

# Read the configuration file
config = configparser.ConfigParser()
config.read('../conf.ini')

# Define the MySQL connection using SQLAlchemy
db_url = f"mysql+mysqlconnector://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}/{config['database']['name']}"
engine = sqlalchemy.create_engine(db_url)
Session = sessionmaker(bind=engine)

_start = time.time()

def log_in_out(func):
    # Decorator to log function calls
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
def read_csv(file_path):
    # Read the CSV file and convert it to a DataFrame
    df = pd.read_csv(file_path)
    return df

@log_in_out
def clean_data(df):
    # Placeholder for data cleaning operations
    # Implement any specific data cleaning here
    return df

@log_in_out
def write_to_db(dataframe, table_name):
    session = Session()
    try:
        dataframe.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

@log_in_out
def process_csv_files(directory):
    for file_name in os.listdir(directory):
        if file_name.endswith(".csv"):
            file_path = os.path.join(directory, file_name)
            table_name = os.path.splitext(file_name)[0]  # Use the file name (without extension) as table name
            df = read_csv(file_path)
            df = clean_data(df)
            write_to_db(df, table_name)

process_csv_files(config["sources"]["directorycsv"])

print(
    f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} - [END INIT]: Data Import done in {round(time.time() - _start)}")
