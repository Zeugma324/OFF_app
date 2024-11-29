"""
Ce fichier main contient l'instancialisation des connexions et 
requetages des différentes base de données.
Il contient également les requêtes GET.
"""

from fastapi import FastAPI
import duckdb
from pymongo import MongoClient
import mysql.connector
from mysql.connector import Error

app = FastAPI()

con = duckdb.connect()

PARQUET_FILE = "data/produits_filtrés.parquet"

mongo_client = MongoClient("mongodb://mongo:27017")
db = mongo_client["my_mongodb"]
recipes_collection = db["recipes"]


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


@app.get("/heartbeat")
async def get_app_name():
    """
    Retourne le nom de l'application
    """

    return {"nomApplication": "The best Milky way recipe guide"}


@app.get("/extracted_data")
async def get_product_count():
    """
    Retourne le nombre de produits alimentaire scannées, le nombre de recettes
    ainsi que le nombre d'aliments de base dans les bases de données
    """

    query = f"SELECT COUNT(*) AS product_count FROM '{PARQUET_FILE}'"
    result = con.execute(query).fetchone()
    product_count = result[0]

    nb_recettes_cuisine = recipes_collection.count_documents({})

    mysql_conn = create_connection(
        "ingredients", "api_endpoint", "abracadabra", "raw_ingredients"
    )
    nb_produits_alimentaires_de_base = 0
    if mysql_conn:
        base_query = "SELECT COUNT(*) FROM food_name WHERE EstAlimentDeBase = 1;"
        cursor = mysql_conn.cursor()
        cursor.execute(base_query)
        nb_produits_alimentaires_de_base = cursor.fetchone()[0]
        cursor.close()
        mysql_conn.close()

    return {
        "nbProduitsAlimentairesScannes": product_count,
        "nbProduitsAlimentairesDeBase": nb_produits_alimentaires_de_base,
        "nbRecettesCuisine": nb_recettes_cuisine,
    }


@app.get("/transformed_data")
async def categories_et_indicateurs():
    """
    Retourne le nombre d'enregistrement possedant un nutriscore, un novascore et un ecoscore.
    Retourne également les catégories des produits ainsi que le compte associé.
    """

    query_1 = f"""SELECT
        COUNT(*) AS count_nutriscore
        FROM '{PARQUET_FILE}'
        WHERE nutriscore_grade IN ('a', 'b', 'c', 'd', 'e')"""

    query_2 = f"""
        SELECT 
        COUNT(*) AS count_nova_groups
        FROM '{PARQUET_FILE}'
        WHERE nova_groups IN ('1', '2', '3', '4')"""

    query_3 = f"""
        SELECT 
        COUNT(*) AS count_ecoscore
        FROM '{PARQUET_FILE}'
        WHERE ecoscore_grade IN ('a', 'b', 'c', 'd', 'e')
        """

    query_4 = f"""SELECT SUBSTRING(categories, 4, LEN(categories)), COUNT(*)
        FROM (SELECT UNNEST(food_groups_tags) AS categories 
            FROM '{PARQUET_FILE}') AS categories_list 
        GROUP BY categories 
        ORDER BY COUNT(*) DESC"""

    count_nutriscore = con.execute(query_1).fetchone()[0]
    count_nova = con.execute(query_2).fetchone()[0]
    count_ecoscore = con.execute(query_3).fetchone()[0]

    categories_count = con.execute(query_4).fetchall()

    categories_list = {}

    for categorie, count in categories_count:
        categories_list[categorie] = count

    return {
        "indicateursDeQualite": {
            "Nutriscore": count_nutriscore,
            "Nova": count_nova,
            "EcoScore": count_ecoscore,
        },
        "categoriesProduitAlimentaire": categories_list,
    }
