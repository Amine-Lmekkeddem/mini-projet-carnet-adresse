"""
auth.py — Module d'authentification (SQLite)
Remplace l'ancienne version JSON.
Utilise bcrypt (rounds=12) pour le hachage des mots de passe.
Les comptes admins sont stockés dans la table 'admins' de contacts.db
"""

import bcrypt
from database import (
    init_db,
    admin_ajouter, admin_hash, admin_mettre_a_jour_hash,
    admin_supprimer, admin_compter, admin_liste,
)

# ── Initialisation automatique ────────────────────────────────────────────

# ── Hachage ───────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    """Retourne le hash bcrypt (str) d'un mot de passe en clair."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _bootstrap():
    """Crée la DB si absente, insère l'admin par défaut si la table est vide."""
    init_db()
    if admin_compter() == 0:
        admin_ajouter("admin", _hash_password("Admin1234!"))

_bootstrap()


def _verify_password(plain: str, hashed: str) -> bool:
    """Vérifie si un mot de passe en clair correspond au hash bcrypt stocké."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Politique de mot de passe ─────────────────────────────────────────────

_SPECIALS = set("!@#$%^&*()_+-=[]{}|;':\",./<>?")

def _validate_password(password: str) -> None:
    """
    Lève ValueError si le mot de passe ne respecte pas la politique :
    ≥ 8 caractères · 1 majuscule · 1 chiffre · 1 caractère spécial
    """
    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
    if not any(c.isupper() for c in password):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule.")
    if not any(c.isdigit() for c in password):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
    if not any(c in _SPECIALS for c in password):
        raise ValueError("Le mot de passe doit contenir au moins un caractère spécial.")


# ── API publique ──────────────────────────────────────────────────────────

def authenticate(username: str, password: str) -> bool:
    """Retourne True si les identifiants sont valides."""
    hashed = admin_hash(username)
    if hashed is None:
        return False
    return _verify_password(password, hashed)


def add_admin(username: str, password: str) -> bool:
    """Ajoute un admin. Retourne False si username déjà pris.
    Lève ValueError si le mot de passe ne respecte pas la politique."""
    _validate_password(password)
    return admin_ajouter(username, _hash_password(password))


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Change le mot de passe après vérification de l'ancien."""
    if not authenticate(username, old_password):
        return False
    _validate_password(new_password)
    return admin_mettre_a_jour_hash(username, _hash_password(new_password))


def delete_admin(username: str) -> bool:
    """Supprime un admin. Lève ValueError si c'est le dernier compte."""
    if admin_compter() <= 1:
        raise ValueError("Impossible de supprimer le dernier administrateur.")
    return admin_supprimer(username)


def list_admins() -> list[str]:
    """Retourne la liste des noms d'utilisateurs administrateurs."""
    return admin_liste()