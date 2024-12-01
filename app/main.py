"""
Ce fichier main contient l'instancialisation des connexions et 
requetages des différentes base de données.
Il contient également les requêtes GET.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app import (
    recipes_collection,
    con,
    PARQUET_FILE,
    create_connection,
)

app = FastAPI()


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

@app.get("/type")
async def get_type():

    return {"beverages",
            "breakfast",
            "main-dish",
            "desserts",
            "snacks", 
            "appetizers", 
            "side-dishes",
            "60-minutes-or-less",
            "30-minutes-or-less",
            "4-hours-or-less",
            "15-minutes-or-less",
            "vegetables",
            "meat",
            "dietary",
            "3-steps-or-less"}

#definition du modele pydantic pour le payload
class RecipesRequest(BaseModel):
    type: List[str] = []

class RecipesResponse(BaseModel):
    nom: str
    ingredients: List[str]
    description: str

@app.post("/recette", response_model=RecipesResponse)
async def get_recette(request: RecipesRequest):
    types_recherche = request.type

    query = {}
    if types_recherche:
        query["tags"] = {"$in" : types_recherche}
        
        recette = recipes_collection.find_one(query, {"name": 1, "ingredients": 1, "description": 1})

        if not recette:
            raise HTTPException(status_code=404, detail="Aucune recette trouvée pour les types donnés.")

        return RecipesResponse(
            nom=recette["name"],
            ingredients=recette["ingredients"],
            description=recette.get("description", "Aucune description disponible.")
        )