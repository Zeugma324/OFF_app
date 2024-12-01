from pymongo import MongoClient
import duckdb
import mysql.connector
from mysql.connector import Error

# Connexion MongoDB
mongo_client = MongoClient("mongodb://mongo:27017")
db = mongo_client["my_mongodb"]
recipes_collection = db["recipes"]

# Connexion DuckDB
con = duckdb.connect()
PARQUET_FILE = "data/produits_filtrés.parquet"

# fonctions mysql
def create_connection(host_name, user_name, user_password, db_name):
    """
    Fonction qui créé une connexion a la base de données MySQL
    """

    connexion = None
    try:
        connexion = mysql.connector.connect(
            host=host_name, user=user_name, passwd=user_password, database=db_name
        )
        if connexion.is_connected():
            print("Connexion réussie à MySQL")
    except Error as e:
        print(f"Erreur lors de la connexion à MySQL : {e}")

    return connexion


def execute_query(connexion, query):
    """
    Fonction qui execute une requete sur la base de données MySQL,
    prend la connexion et la requete en parametre
    """

    cursor = connexion.cursor()
    try:
        cursor.execute(query)
        connexion.commit()
        print("Requête exécutée avec succès")
    except Error as e:
        print(f"Erreur lors de l'exécution de la requête : {e}")