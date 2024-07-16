import os
from dotenv import load_dotenv
import mysql.connector

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

try:
    conn = mysql.connector.connect(**config)
    if conn.is_connected():
        print("Connexion à la base de données réussie")
        conn.close()
except mysql.connector.Error as err:
    print(f"Erreur de connexion à la base de données : {err}")
