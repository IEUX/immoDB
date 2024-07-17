# immoDB

## Configuration

Créez un fichier `.env` à la racine contenant les informations suivantes :

```plaintext
DB_HOST=à remplir
DB_USER=à remplir
DB_PASSWORD=à remplir
DB_NAME=à remplir
SOURCES_DIRECTORY=./data
SOURCES_DIRECTORYCSV=./data/csv
SOURCES_TRANSACTIONS=./data/transactions.npz
MAX_PRICE=69000000
MIN_PRICE=25000
```

## Dependences

Pour installer les dépendences python il vous suffit d'executer la commande ```pip install -r requirements.txt```

## Lancer l'application - Dev

A la racine du projet executer la commande ```python3 App/main.py```

## Lancer l'application - Prod

Installer **gunicorn**: ```pip install gunicorn```

Executer la commande ```gunicorn --chdir App/ main:server```