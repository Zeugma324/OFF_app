import ast
from pymongo import MongoClient

mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["my_mongodb"]
recipes_collection = db["recipes"]  

for doc in recipes_collection.find():
    update_fields = {}

    tags_str = doc.get("tags")
    if isinstance(tags_str, str):
        try:
            tags_list = ast.literal_eval(tags_str)
            if isinstance(tags_list, list):
                update_fields["tags"] = tags_list
        except Exception as e:
            print(f"Erreur conversion tags doc {doc['_id']}: {e}")

    ingredients_str = doc.get("ingredients")
    if isinstance(ingredients_str, str):
        try:
            ingredients_list = ast.literal_eval(ingredients_str)
            if isinstance(ingredients_list, list):
                update_fields["ingredients"] = ingredients_list
        except Exception as e:
            print(f"Erreur conversion ingrédients doc {doc['_id']}: {e}")

    if update_fields:
        recipes_collection.update_one({"_id": doc["_id"]}, {"$set": update_fields})

print("Conversion terminée")
