"""
Ce fichier main contient l'instancialisation des connexions et 
requetages des différentes base de données.
Il contient également les requêtes GET et POST.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from rapidfuzz.process import extract
from rapidfuzz.fuzz import partial_ratio
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
    """
    méthode GET pour récuperer les types disponible de recette.

    Returns:
        Un JSON contenant les types de recettes disponible.
    """
    return {
        "beverages",
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
        "3-steps-or-less",
    }


@app.get("/readme")
async def get_readme():
    """
    Retourne le fichier README.md.
    """
    readme_path = Path("app/README.md")
    
    if not readme_path.exists():
        raise HTTPException(status_code=404, detail="Fichier README.md introuvable.")
    
    return FileResponse(readme_path, media_type="text/markdown", filename="README.md")


# definition du modele pydantic pour le payload
class RecipesRequest(BaseModel):
    """
    Template de la requête POST /recette

    Attribute :
        type: List[str] : Liste des types de la recette
    """

    type: List[str] = []


class RecipesResponse(BaseModel):
    """
    Template de la réponse à la requête POST /recette

    Attributes :
        nom: str : nom de la recette
        ingredients: List[str] : Liste des ingrédients de la recette
        description: str : description de la recette
    """

    nom: str
    ingredients: List[str]
    description: str
    # tags: List[str]


@app.post("/recette", response_model=RecipesResponse)
async def get_recette(request: RecipesRequest):
    """
    POST query permettant d'obtenir une recette
    aléatoire parmis celle disponible selon les critères établit.

    Args:
        request (RecipesRequest): La requete contenant les types de recette à rechercher

    Returns:
        RecipesResponse: JSON contenant le nom, ingrédients et description de la recette.
    """
    types_recherche = request.type

    query = {}
    if types_recherche:
        query["tags"] = {"$all": types_recherche}

    pipeline = [
        {"$match": query},
        {"$sample": {"size": 1}},
        {"$project": {"name": 1, "ingredients": 1, "description": 1, "tags": 1}},
    ]

    recette_list = list(recipes_collection.aggregate(pipeline))
    local_recette = recette_list[0]

    if not local_recette:
        raise HTTPException(
            status_code=404, detail="Aucune recette trouvée pour les types donnés."
        )

    return RecipesResponse(
        nom=local_recette["name"],
        ingredients=local_recette["ingredients"],
        description=local_recette.get("description", "Aucune description disponible."),
        # tags=recette["tags"]
    )


class Recette(BaseModel):
    """
    Modèle d'une recette.

    Attributes:
        nomProduit (str): nom du produit
        ingredients (List[str]): liste des ingrédients de la recette
        description (Optional[str]): description optionnelle de la recette
    """

    nomProduit: str = Field(alias="nom")
    ingredients: List[str]
    description: Optional[str]


class IndicateursDeQualite1(BaseModel):
    """
    Modèle des indicateurs d'un produit.

    Attributes:
        Nutriscore (Optional[str]): le nutriscore (optionnel).
        Nova (Optional[str]): le nova score (optionnel).
        Ecoscore (Optional[str]): l'ecoscore (optionnel).
    """

    Nutriscore: Optional[str]
    Nova: Optional[str]
    Ecoscore: Optional[str]


class CuisinerRequest(BaseModel):
    """
    Modèle de recommandation de produits.

    Attributes:
        recette (Recette): la recette de base pour les recommandations.
        preferenceMarqueProduit (Optional[str]): la marque de preference
            de l'utilisateur (optionnel)
        indicateursDeQualiteSuperieurA (Optional[IndicateursDeQualite1]):
        les indicatgeurs de qualité de préference de l'utilisateur (otpionnel)
    """

    recette: Recette
    preferenceMarqueProduit: Optional[str] = None
    indicateursDeQualiteSuperieurA: Optional[IndicateursDeQualite1] = None


class RecoProduit(BaseModel):
    """
    Modèle de recommandation d'un produit.

    Attributes:
        nomProduit (str): nom du produit.
        indicateursDeQualite (Optional[IndicateursDeQualite1]):
            les indicateurs de qualité du produit.
        marque (Optional[str]): marque du produit.
        categories (Optional[List[str]]): catégories du produit.
        produitDeBase (bool): Indique si le produit est un aliment de base.
    """

    nomProduit: str
    indicateursDeQualite: Optional[IndicateursDeQualite1] = None
    marque: Optional[str] = None
    categories: Optional[List[str]] = None
    produitDeBase: bool


class CuisinerResponse(BaseModel):
    """
    Modèle de la réponse de recommandation du produit.

    Attributes:
        data (Dict[str, List[RecoProduit]]):
        dictionnaire des recommandations pour chaque ingrédient.
    """

    data: Dict[str, List[RecoProduit]]


def query_constructor(request, ing):
    """
    Construit une requête SQL en fonction des
    paramètres utilisateur et de l'ingrédient donné.

    Args:
        request: Données de la requête utilisateur.
        ing: Ingrédient à rechercher.

    Returns:
        Une chaîne de caractères contenant la requête SQL.
    """

    preference = request.preferenceMarqueProduit
    indicateurs = request.indicateursDeQualiteSuperieurA

    query = f"""
        SELECT product_name, ecoscore_grade, nutriscore_grade, nova_groups, brands_tags, categories
        FROM '{PARQUET_FILE}' WHERE product_name ILIKE '%{ing}%'
        """

    if indicateurs and indicateurs.Ecoscore:
        ecoscore_values = ", ".join(f"'{e}'" for e in indicateurs.Ecoscore)
        ecoscore_clause = f" AND ecoscore_grade IN ({ecoscore_values})"
        query += ecoscore_clause
    else:
        query += " AND ecoscore_grade IS NOT NULL"

    if indicateurs and indicateurs.Nutriscore:
        nutriscore_values = ", ".join(f"'{n}'" for n in indicateurs.Nutriscore)
        nutriscore_clause = f" AND nutriscore_grade IN ({nutriscore_values})"
        query += nutriscore_clause
    else:
        query += " AND nutriscore_grade IS NOT NULL"

    if indicateurs and indicateurs.Nova:
        nova_values = ", ".join(str(n) for n in indicateurs.Nova)
        nova_clause = f" AND nova_groups IN ({nova_values})"
        query += nova_clause
    else:
        query += " AND nova_groups IS NOT NULL"

    if preference:
        preference_clause = f""" AND EXISTS (
            SELECT *
            FROM UNNEST(brands_tags) AS brand
            WHERE CAST(brand AS VARCHAR) ILIKE '%{preference}%'
            )"""
        query += preference_clause
    else:
        query += " AND brands_tags IS NOT NULL"

    query += """
        ORDER BY 
            nutriscore_grade ASC NULLS LAST,
            ecoscore_grade ASC NULLS LAST,
            nova_groups ASC NULLS LAST
    """
    query += " LIMIT 5"

    print("Generated Query:")
    print(query)

    return query


@app.post("/cuisiner", response_model=CuisinerResponse)
async def get_cuisiner(request: CuisinerRequest):
    """
    POST query pour obtenir des recommandations de produits en fonction d'une recette.

    Args:
        request (CuisinerRequest): requête contenant
            les informations sur la recette et les préférences utilisateur.

    Returns:
        CuisinerResponse: réponse contenant les recommandations
            de produits pour chaque ingrédient de la recette.
    """
    recette = request.recette

    mysql_conn = create_connection(
        "ingredients", "api_endpoint", "abracadabra", "raw_ingredients"
    )

    response = {}
    for i in recette.ingredients:

        base_aliment = False

        if mysql_conn:
            base_query = f"""
                SELECT FoodDescription 
                FROM food_name 
                WHERE EstAlimentDeBase = 1 
                AND FoodDescription LIKE '{i}%' LIMIT 1;
                """
            print("sql :", i)
            cursor = mysql_conn.cursor()
            cursor.execute(base_query)
            base = cursor.fetchall()

        if base:
            for row in base:
                base = row[0]
                base_aliment = True

        if not base_aliment:
            query = query_constructor(request, i)
            results = con.execute(query).fetchall()
            print("COMO ESTA")
            print(results)

            if not results:
                print(
                    f"""
                      Pas de résultat pour l'ingredient : {i}. 
                      Utilisation de rapidfuzz pour une recherche approximative...
                      """
                )
                # Charger tous les produits pour une recherche approximative
                all_products_query = f"""
                    SELECT product_name, ecoscore_grade, nutriscore_grade, nova_groups, brands_tags, categories 
                    FROM '{PARQUET_FILE}' 
                    WHERE LENGTH(product_name) > 4
                    ORDER BY 
                        ecoscore_grade ASC NULLS LAST,
                        nutriscore_grade ASC NULLS LAST,
                        nova_groups ASC NULLS LAST
                    """
                all_products = con.execute(all_products_query).fetchall()

                # Utiliser RapidFuzz pour trouver les correspondances les plus proches
                product_names = [row[0] for row in all_products]
                matches = extract(i, product_names, limit=5, scorer=partial_ratio)

                # Extraire les informations des correspondances
                results = [
                    row
                    for row in all_products
                    if row[0] in [match[0] for match in matches]
                ]
                print("Meilleurs matchs rapidfuzz :", matches)

        if i not in response:
            response[i] = []

        if base_aliment:
            response[i].append(
                RecoProduit(
                    nomProduit=base,
                    indicateursDeQualite=None,
                    marque=None,
                    categories=None,
                    produitDeBase=True,
                )
            )
        else:
            for row in results:
                product_name, ecoscore, nutriscore, nova, brands, categories = row

                if isinstance(categories, str):
                    categories = categories.split(", ")
                if brands:
                    brands = brands[0]

                response[i].append(
                    RecoProduit(
                        nomProduit=product_name,
                        indicateursDeQualite=IndicateursDeQualite1(
                            Nutriscore=nutriscore or None,
                            Nova=nova or None,
                            Ecoscore=ecoscore or None,
                        ),
                        marque=brands or None,
                        categories=categories or None,
                        produitDeBase=False,
                    )
                )
        base = []
    cursor.close()
    mysql_conn.close()
    return CuisinerResponse(data=response)
