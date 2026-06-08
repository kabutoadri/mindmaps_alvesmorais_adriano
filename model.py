# Projet mindmaps : prototype d'affichage de mindmap en radial et forum 
# JCY et Adriano Alves Morais (projet Python) - 2025-2026 -v1.0
# 08 juin 2026
# model.py : définition des fonctions pour interagir avec la base de données

import mysql.connector
import bcrypt
from utils.config import get_db_config

# Fonction pour obtenir une connexion à la base de données
def get_connection(db_mode="local"):
    cfg = get_db_config(db_mode)
    return mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=cfg["port"]
    )

# renvoie le résultat d'une requête SQL en mode dictionnaire
def fetch_all(sql_query, params=None, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    if params:
        cursor.execute(sql_query, params)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    db.close()
    return rows


# renvoie la liste des maps (sans les nodes) pour l'affichage de la page d'accueil
def get_maps(db_mode):
    return fetch_all("select id, title, author_id from maps", None, db_mode)


# renvoie la liste de tous les nodes d'un map (avec le pseudo de l'auteur et sa couleur)
def get_nodes_for_map(map_id, db_mode):
    return fetch_all("select nodes.id, nodes.map_id, parent_id, author_id, text, nodes.level,users.color " \
    "from nodes inner join users on nodes.author_id = users.id " \
    "where map_id=%s", (map_id,), db_mode)

# renvoie la liste des users
def get_users(db_mode):
    return fetch_all("select id, pseudo, level from users", None, db_mode)

# renvoie la liste des nodes
def get_nodes(db_mode):
    return fetch_all("select map_id, parent_id, author_id, text, level from nodes", None, db_mode)

# fonction pour éditer un node
def edit_node_db(text, node_id, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("UPDATE nodes SET text=%s WHERE id=%s",(text, node_id))
    db.commit()
    db.close()

# fonction pour supprimer des nodes
def delete_node_db(node_id, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE from nodes WHERE id=%s", (node_id,))
    db.commit()
    db.close()

# fonction pour ajouter un node en dessous du node parent
def insert_node_db(map_id, parent_id, author_id, text, level, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("INSERT INTO nodes (map_id, parent_id, author_id, text, level) VALUES (%s, %s, %s, %s, %s)",(map_id, parent_id, author_id, text, (level+1)))
    db.commit()
    db.close()

# fonctions pour insérer, mettre à jour et supprimer des maps
# fonction pour insérer une map (retourne l'id du node créé)
def edit_map_db(title, map_id, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("UPDATE maps SET title=%s WHERE id=%s",(title, map_id))
    db.commit()
    db.close()

# fonction pour supprimer des maps
def delete_map_db(map_id, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE from maps WHERE id=%s", (map_id,))
    db.commit()
    db.close()

# fonction pour ajouter une map supplémentaire avec un node parent par défaut
def insert_map_db(title, author_id, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("INSERT INTO maps (title, author_id) VALUES (%s, %s)",(title, author_id))
    db.commit()
    new_map_id = cursor.lastrowid # récupère la nouvelle map id
    db.close()
    return new_map_id # retourne la nouvelle map id pour créer le node principal à la création de la map

# fonction pour vérifier les identifiants de connexion d'un utilisateur (retourne les infos de l'utilisateur si ok, sinon None)
def check_login(pseudo, password, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, pseudo, hash, level FROM users WHERE pseudo=%s", (pseudo,))
    row = cursor.fetchone()
    db.close()
    if not row:
        return None
    stored = row["hash"]
    if isinstance(stored, str):
        stored = stored.encode()
    # Vérifier le mot de passe avec bcrypt
    if bcrypt.checkpw(password.encode(), stored):
        return row
    return None

# fonction qui vérifie si le pseudo est déjà dans la base de données
def check_register(pseudo, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT pseudo FROM users WHERE pseudo=%s", (pseudo,))
    row = cursor.fetchone()
    db.close()
    if row:
        return row
    return None

# fonction pour enregistrer un nouvel utilisateur (pseudo, mot de passe hashé, couleur)
def save_register(pseudo, get_password, color, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    password = bcrypt.hashpw(get_password.encode(), bcrypt.gensalt())  # chiffrement du mot de passe
    cursor.execute("INSERT INTO users (pseudo, hash, level, color) VALUES (%s, %s, %s, %s)", (pseudo, password, 1, color))
    db.commit()
    db.close()

# fonction pour récupérer un profil utilisateur en particulier
def get_user_profile(user_id, db_mode="local"):
    return fetch_all(
        "SELECT id, pseudo, color FROM users WHERE id=%s",
        (user_id,),
        db_mode
    )

# fonction pour mettre à jour le nouveau profil
def update_user_profile(user_id, pseudo, color, hash, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    if hash is None:
        cursor.execute("UPDATE users SET pseudo=%s, color=%s WHERE id=%s", (pseudo, color, user_id))
    else:
        password = bcrypt.hashpw(hash.encode(), bcrypt.gensalt())  # chiffrement du mot de passe
        cursor.execute("UPDATE users SET pseudo=%s, hash=%s, color=%s WHERE id=%s", (pseudo, password, color, user_id))
    db.commit()
    db.close()