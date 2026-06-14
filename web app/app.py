"""
app.py — Flask Web App : Carnet d'adresses
Fonctionnalités : login, CRUD contacts, recherche, CSV import/export, gestion admins
Base de données : SQLite3 (contacts.db)
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_file
)
import sqlite3
import os
import re
import csv
import io
import hashlib
import hmac
import secrets
import urllib.parse
from datetime import datetime
from contextlib import contextmanager
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

app.jinja_env.filters['urldecode'] = urllib.parse.unquote

DB_PATH = os.path.join(os.path.dirname(__file__), "contacts.db")

# ═══════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telephone TEXT NOT NULL UNIQUE,
                date_ajout TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                date_creation TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_contacts_nom
            ON contacts(nom COLLATE NOCASE);
        """)

    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO admins (username, password_hash, date_creation) VALUES (?, ?, ?)",
                ("admin", _hash_password("Admin1234!"), now())
            )

# ═══════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════

def _hash_password(plain: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 310000)
    return f"{salt}${h.hex()}"

def _verify_password(plain: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$")
        expected = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 310000)
        return hmac.compare_digest(h, expected.hex())
    except:
        return False

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ═══════════════════════════════════════════════
#  CONTACT VALIDATION
# ═══════════════════════════════════════════════

EMAIL_RE = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

def validate_contact(nom, email, telephone):
    errors = []
    if not nom.strip():
        errors.append("Nom requis")
    if not EMAIL_RE.match(email.strip()):
        errors.append("Email invalide")
    if not (telephone.strip().isdigit() and len(telephone.strip()) == 10):
        errors.append("Téléphone invalide")
    return errors

# ═══════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════

@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as conn:
            row = conn.execute(
                "SELECT password_hash FROM admins WHERE username=?",
                (username,)
            ).fetchone()

        if row and _verify_password(password, row["password_hash"]):
            session["user"] = username
            return redirect(url_for("index"))

        error = "Identifiants incorrects"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ═══════════════════════════════════════════════
#  CONTACTS
# ═══════════════════════════════════════════════

@app.route("/contacts")
@login_required
def index():
    q = request.args.get("q", "").strip()

    with get_db() as conn:
        if q:
            like = f"%{q}%"
            contacts = conn.execute("""
                SELECT * FROM contacts
                WHERE nom LIKE ? OR email LIKE ? OR telephone LIKE ?
                ORDER BY nom
            """, (like, like, like)).fetchall()
        else:
            contacts = conn.execute(
                "SELECT * FROM contacts ORDER BY nom"
            ).fetchall()

    return render_template("index.html",
                           contacts=[dict(c) for c in contacts],
                           user=session["user"],
                           q=q)

@app.route("/contacts/add", methods=["GET", "POST"])
@login_required
def add_contact():
    if request.method == "POST":
        nom = request.form.get("nom", "")
        email = request.form.get("email", "")
        telephone = request.form.get("telephone", "")

        errors = validate_contact(nom, email, telephone)
        if errors:
            return render_template("form.html", errors=errors)

        try:
            with get_db() as conn:
                conn.execute("""
                    INSERT INTO contacts (nom, email, telephone, date_ajout)
                    VALUES (?, ?, ?, ?)
                """, (nom, email.lower(), telephone, now()))

            flash("Contact ajouté", "success")
            return redirect(url_for("index"))

        except sqlite3.IntegrityError:
            flash("Email ou téléphone déjà utilisé", "error")

    return render_template("form.html", errors=[])

@app.route("/contacts/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_contact(id):
    with get_db() as conn:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id=?",
            (id,)
        ).fetchone()

    if not contact:
        return redirect(url_for("index"))

    if request.method == "POST":
        nom = request.form.get("nom", "")
        email = request.form.get("email", "")
        telephone = request.form.get("telephone", "")

        with get_db() as conn:
            conn.execute("""
                UPDATE contacts
                SET nom=?, email=?, telephone=?
                WHERE id=?
            """, (nom, email, telephone, id))

        flash("Contact modifié", "success")
        return redirect(url_for("index"))

    return render_template("form.html", contact=dict(contact))

@app.route("/contacts/delete/<int:id>", methods=["POST"])
@login_required
def delete_contact(id):
    with get_db() as conn:
        conn.execute("DELETE FROM contacts WHERE id=?", (id,))
    flash("Contact supprimé", "success")
    return redirect(url_for("index"))

# ═══════════════════════════════════════════════
#  CSV
# ═══════════════════════════════════════════════

@app.route("/contacts/export")
@login_required
def export_csv():
    with get_db() as conn:
        data = conn.execute("SELECT * FROM contacts").fetchall()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "nom", "email", "telephone", "date_ajout"])
    writer.writeheader()
    for row in data:
        writer.writerow(dict(row))

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="contacts.csv"
    )

@app.route("/contacts/import", methods=["POST"])
@login_required
def import_csv():
    file = request.files.get("csv_file")

    if not file:
        return redirect(url_for("index"))

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    with get_db() as conn:
        for row in reader:
            try:
                conn.execute("""
                    INSERT INTO contacts (nom, email, telephone, date_ajout)
                    VALUES (?, ?, ?, ?)
                """, (row["nom"], row["email"], row["telephone"], now()))
            except:
                pass

    flash("Import terminé", "success")
    return redirect(url_for("index"))

# ═══════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════

@app.route("/admin")
@login_required
def admin():
    with get_db() as conn:
        admins = conn.execute("SELECT username FROM admins").fetchall()
    return render_template("admin.html", admins=[a["username"] for a in admins])

@app.route("/admin/add", methods=["POST"])
@login_required
def admin_add():
    username = request.form.get("username")
    password = request.form.get("password")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO admins (username, password_hash, date_creation)
            VALUES (?, ?, ?)
        """, (username, _hash_password(password), now()))

    return redirect(url_for("admin"))

# ═══════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    app.run(debug=True)