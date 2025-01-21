
# Documentation de l'API

## Introduction

Cette API permet de gérer une base de données alimentaire canadienne basé sur les bases de données d'OpenFoodFacts et de la FCEN, de fournir des informations nutritionnelles et des recommandations personnalisées pour les utilisateurs. Elle se compose de plusieurs endpoints conçus pour différents besoins, notamment l'extraction de données, la transformation d`indicateurs nutritionnels et les suggestions de produits pour une recette donnée.

## Fonctionnalités Principales

### Endpoints Disponibles

- **`GET /heartbeat`** : Retourne le nom de l`application.
- **`GET /extracted_data`** :
  - Fournit des statistiques sur :
    - Le nombre de produits alimentaires scannés.
    - Le nombre de recettes disponibles.
    - Le nombre d`aliments de base dans la base de données.
- **`GET /transformed_data`** :
  - Retourne :
    - Le nombre d`enregistrements avec un NutriScore, un NovaScore et un EcoScore.
    - Les catégories de produits et leur quantité.
- **`GET /readme`** : Affiche le contenu du fichier `README.md`.
- **`POST /recette`** : Permet de récupérer une recette basée sur les types.
- **`POST /cuisiner`** : Suggestion de produits en fonction des préférences utilisateur et d'une recette.


### Exemples d`Utilisation

#### Exemple de Requête pour Obtenir des Recettes
**Requête :**
```json
POST /recette
{
  "type": ["meat", "15-minutes-or-less"]
}
```
**Réponse :**
```json
{
    "nom": "oriental chicken summer salad",
    "ingredients": [
        "cooked chicken",
        "cooked rice",
        "cucumber",
        "red capsicum",
        "tomatoes",
        "canned corn kernels",
        "chives",
        "soy sauce",
        "lemon juice",
        "olive oil",
        "coriander"
    ],
    "description": "this is a great salad to make for a lunchbox. the ingredients are simple so most people would have these on hand & it is nice & filling & full of goodness. i've also made this with tuna which is great."
}
```

#### Exemple de Requête pour Obtenir des Produits en Fonction des Préférences
**Requête :**
```json
POST /cuisiner
{
    "recette": {
    "nom": "the cake mix doctor   peanut butter brownies",
    "ingredients": [
        "brownie mix",
        "crunchy peanut butter",
        "butter",
        "eggs",
        "semi-sweet chocolate chips",
        "sweetened condensed milk",
        "pure vanilla extract"
    ],
    "description": "this sweet recipe comes from ‘the cake mix doctor returns’. it was fun to make and was a great hit at work.  i used a fudge brownie mix and the brownies almost tasted like peanut butter fudge."
    },
    "preferenceMarqueProduit": "Marque A",
    "indicateursDeQualiteSuperieurA": {
        "Nutriscore": "A",
        "Nova": "1",
        "Ecoscore": "A"
    }
}

```
**Réponse :**
```json
{
    "data": {
        "brownie mix": [
            {
                "nomProduit": "Brownie mix",
                "indicateursDeQualite": {
                    "Nutriscore": "c",
                    "Nova": null,
                    "Ecoscore": "e"
                },
                "marque": null,
                "categories": [
                    "Snacks",
                    "Snacks sucrés",
                    "Biscuits et gâteaux",
                    "Gâteaux",
                    "Gâteaux au chocolat",
                    "Brownies"
                ],
                "produitDeBase": false
            },
            {
                "nomProduit": "Gluten-free brownie mix",
                "indicateursDeQualite": {
                    "Nutriscore": "d",
                    "Nova": null,
                    "Ecoscore": "e"
                },
                "marque": "bob-s-red-mill",
                "categories": [
                    "Snacks",
                    "Snacks sucrés",
                    "Biscuits et gâteaux",
                    "Gâteaux",
                    "Gâteaux au chocolat",
                    "Brownies"
                ],
                "produitDeBase": false
            },
            {
                "nomProduit": "Brownie mix baking kit",
                "indicateursDeQualite": {
                    "Nutriscore": "e",
                    "Nova": null,
                    "Ecoscore": "e"
                },
                "marque": "oreo",
                "categories": [
                    "Snacks",
                    "Snacks sucrés",
                    "Biscuits et gâteaux",
                    "Gâteaux",
                    "Gâteaux au chocolat",
                    "Brownies"
                ],
                "produitDeBase": false
            },
            {
                "nomProduit": "Brownie mix",
                "indicateursDeQualite": {
                    "Nutriscore": "unknown",
                    "Nova": null,
                    "Ecoscore": "unknown"
                },
                "marque": null,
                "categories": null,
                "produitDeBase": false
            }]
            "etc..."
      }
    }
```

## Configuration

### Pré-requis
- Python 3.9+
- FastAPI
- Outils pour tester l'API (comme Postman ou cURL)

### Installation
1. Clonez ce dépôt.
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Lancez l`API :
   ```bash
   uvicorn main:app --reload
   ```
