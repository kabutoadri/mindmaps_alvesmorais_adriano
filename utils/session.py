# Projet mindmaps : prototype d'affichage de mindmap en radial et forum 
# JCY pour SI-CA1 (projet Python) - 2025-2026
# 13 avril 2026
# Modifications : Adriano Alves Morais, le 04.05.2026
# session.py : Gestion de la session utilisateur (stockage du pseudo et du niveau d'accès)

# utils/session.py : gestion de la session utilisateur (stockage du pseudo et du niveau d'accès)
class Session:
    pseudo = None
    level = None
    id = None

    # Méthodes de classe pour gérer la session utilisateur
    @classmethod
    def login(cls, pseudo, level,id):
        cls.pseudo = pseudo
        cls.level = level
        cls.id = id
 
    # Méthode pour vérifier si un utilisateur est connecté
    @classmethod
    def is_authenticated(cls):
        return cls.pseudo is not None
    
    # Méthode pour le logout de l'utilisateur
    @classmethod 
    def logout(cls):
        cls.pseudo = None
        cls.level = None
        cls.id = None

    # Méthode pour vérifier si un utilisateur est déconnecté
    @classmethod
    def is_unauthenticated(cls):
        return cls.pseudo is None
