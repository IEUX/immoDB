import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

try:
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    if connection.is_connected():
        print("Successfully connected to the database")
except Exception as e:
    print(f"Error: {e}")
finally:
    if connection.is_connected():
        connection.close()
