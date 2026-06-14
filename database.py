"""
database.py — Couche d'accès SQLite
Gère deux tables :
  • contacts  (id, nom, email, telephone, date_ajout)
  • admins    (id, username, password_hash, date_creation)

Toutes les données (contacts ET comptes admin) résident dans contacts.db
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "contacts.db"


# ════════════════════════════════════════════════════════════════════════════
#  INITIALISATION
# ════════════════════════════════════════════════════════════════════════════

def init_db(path: str = DB_PATH) -> None:
    """Crée les tables si elles n'existent pas encore."""
    with _connect(path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nom         TEXT    NOT NULL,
                email       TEXT    NOT NULL UNIQUE,
                telephone   TEXT    NOT NULL UNIQUE,
                date_ajout  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admins (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT    NOT NULL UNIQUE,
                password_hash   TEXT    NOT NULL,
                date_creation   TEXT    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_contacts_nom
                ON contacts(nom COLLATE NOCASE);
        """)


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS INTERNES
# ════════════════════════════════════════════════════════════════════════════

@contextmanager
def _connect(path: str = DB_PATH):
    """Context manager : ouvre la connexion, commit ou rollback, ferme."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row          # accès par nom de colonne
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ════════════════════════════════════════════════════════════════════════════
#  CONTACTS
# ════════════════════════════════════════════════════════════════════════════

def contact_ajouter(nom: str, email: str, telephone: str) -> bool:
    """
    Insère un contact. Retourne False si email ou téléphone déjà utilisé.
    """
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO contacts (nom, email, telephone, date_ajout) VALUES (?, ?, ?, ?)",
                (nom.strip(), email.strip().lower(), telephone.strip(), _now())
            )
        return True
    except sqlite3.IntegrityError:
        return False


def contact_tous() -> list[dict]:
    """Retourne tous les contacts triés par nom (insensible à la casse)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contacts ORDER BY nom COLLATE NOCASE"
        ).fetchall()
    return [dict(r) for r in rows]


def contact_rechercher(terme: str) -> list[dict]:
    """Recherche par nom, email ou téléphone (LIKE, insensible à la casse)."""
    like = f"%{terme.strip()}%"
    with _connect() as conn:
        rows = conn.execute(
            """SELECT * FROM contacts
               WHERE  nom       LIKE ? COLLATE NOCASE
                  OR  email     LIKE ? COLLATE NOCASE
                  OR  telephone LIKE ?
               ORDER BY nom COLLATE NOCASE""",
            (like, like, like)
        ).fetchall()
    return [dict(r) for r in rows]


def contact_par_email(email: str) -> dict | None:
    """Retourne le contact correspondant à l'email, ou None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM contacts WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None


def contact_modifier(email_original: str, nom: str, email: str, telephone: str) -> bool:
    """Met à jour un contact. Retourne False si conflit de doublon."""
    try:
        with _connect() as conn:
            cur = conn.execute(
                """UPDATE contacts
                   SET nom=?, email=?, telephone=?
                   WHERE email=?""",
                (nom.strip(), email.strip().lower(),
                 telephone.strip(), email_original.strip().lower())
            )
        return cur.rowcount > 0
    except sqlite3.IntegrityError:
        return False


def contact_supprimer(email: str) -> bool:
    """Supprime le contact par email. Retourne False s'il n'existait pas."""
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM contacts WHERE email = ?", (email.strip().lower(),)
        )
    return cur.rowcount > 0


def contact_compter() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]


# ════════════════════════════════════════════════════════════════════════════
#  ADMINS
# ════════════════════════════════════════════════════════════════════════════

def admin_ajouter(username: str, password_hash: str) -> bool:
    """Insère un compte admin. Retourne False si username déjà pris."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO admins (username, password_hash, date_creation) VALUES (?, ?, ?)",
                (username.strip(), password_hash, _now())
            )
        return True
    except sqlite3.IntegrityError:
        return False


def admin_hash(username: str) -> str | None:
    """Retourne le hash stocké pour cet username, ou None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT password_hash FROM admins WHERE username = ?", (username,)
        ).fetchone()
    return row["password_hash"] if row else None


def admin_mettre_a_jour_hash(username: str, nouveau_hash: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE admins SET password_hash=? WHERE username=?",
            (nouveau_hash, username)
        )
    return cur.rowcount > 0


def admin_supprimer(username: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM admins WHERE username = ?", (username,)
        )
    return cur.rowcount > 0


def admin_compter() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]


def admin_liste() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT username FROM admins ORDER BY date_creation"
        ).fetchall()
    return [r["username"] for r in rows]


# ════════════════════════════════════════════════════════════════════════════
#  EXPORT CSV
# ════════════════════════════════════════════════════════════════════════════

import csv

def exporter_csv(chemin: str, contacts: list[dict] | None = None) -> int:
    """
    Exporte les contacts dans un fichier CSV.
    Si contacts=None, exporte tous les contacts de la base.
    Retourne le nombre de lignes écrites.
    """
    if contacts is None:
        contacts = contact_tous()

    if not contacts:
        return 0

    fieldnames = ["id", "nom", "email", "telephone", "date_ajout"]

    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(contacts)

    return len(contacts)


# ════════════════════════════════════════════════════════════════════════════
#  IMPORT CSV  (synchronisation inverse)
# ════════════════════════════════════════════════════════════════════════════

def importer_csv(chemin: str) -> tuple[int, int]:
    """
    Importe des contacts depuis un CSV (colonnes : nom, email, telephone).
    Les doublons (email ou téléphone) sont ignorés silencieusement.
    Retourne (importés, ignorés).
    """
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    imported, skipped = 0, 0
    with open(chemin, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nom       = row.get("nom", "").strip()
            email     = row.get("email", "").strip()
            telephone = row.get("telephone", "").strip()
            if nom and email and telephone:
                ok = contact_ajouter(nom, email, telephone)
                if ok:
                    imported += 1
                else:
                    skipped += 1
            else:
                skipped += 1

    return imported, skipped