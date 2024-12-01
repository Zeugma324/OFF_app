"""
Module ETL pour le traitement des données de la base de données d'OpenFoodFacts.
"""

import duckdb

con = duckdb.connect()
FICHIER_PARQUET = "data/products.parquet"
con.execute("PRAGMA max_temp_directory_size='30GiB'")
con.execute(
    f"""
    COPY (
        SELECT *
        FROM '{FICHIER_PARQUET}'
        WHERE array_contains(countries_tags, 'en:canada')
    ) TO 'produits_filtrés.parquet' (FORMAT 'parquet')
"""
)

print("Processus ETL terminé !")
