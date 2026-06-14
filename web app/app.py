"""
app.py — Flask Web App : Carnet d'adresses
Fonctionnalités : login, CRUD contacts, recherche, CSV import/export, gestion admins
Base de données : SQLite3 (contacts.db)
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_file, jsonify
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

# Jinja filter to decode URL-encoded strings in templates
app.jinja_env.filters['urldecode'] = urllib.parse.unquote

DB_PATH = os.path.join(os.path.dirname(__file__), "contacts.db")

# ═══════════════════════════════════════════════
#  DATABASE LAYER
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
            CREATE INDEX IF NOT EXISTS idx_contacts_nom ON contacts(nom COLLATE NOCASE);
        """)
    # default admin
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO admins (username, password_hash, date_creation) VALUES (?, ?, ?)",
                ("admin", _hash_password("Admin1234!"), now())
            )

# ═══════════════════════════════════════════════
#  AUTH HELPERS
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
    except Exception:
        return False

def _validate_password(password: str):
    specials = set("!@#$%^&*()_+-=[]{}|;':\",./<>?")
    if len(password) < 8:
        raise ValueError("Au moins 8 caractères requis.")
    if not any(c.isupper() for c in password):
        raise ValueError("Au moins une majuscule requise.")
    if not any(c.isdigit() for c in password):
        raise ValueError("Au moins un chiffre requis.")
    if not any(c in specials for c in password):
        raise ValueError("Au moins un caractère spécial requis.")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════
#  CONTACT HELPERS
# ═══════════════════════════════════════════════

EMAIL_RE = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

def validate_contact(nom, email, telephone):
    errors = []
    if not nom.strip():
        errors.append("Le nom ne peut pas être vide.")
    if not EMAIL_RE.match(email.strip()):
        errors.append("Email invalide.")
    if not (telephone.strip().isdigit() and len(telephone.strip()) == 10):
        errors.append("Le téléphone doit contenir exactement 10 chiffres.")
    return errors

# ═══════════════════════════════════════════════
#  ROUTES — AUTH
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
                "SELECT password_hash FROM admins WHERE username = ?", (username,)
            ).fetchone()
        if row and _verify_password(password, row["password_hash"]):
            session["user"] = username
            return redirect(url_for("index"))
        error = "Identifiants incorrects."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ═══════════════════════════════════════════════
#  ROUTES — CONTACTS
# ═══════════════════════════════════════════════

@app.route("/contacts")
@login_required
def index():
    q = request.args.get("q", "").strip()
    with get_db() as conn:
        if q:
            like = f"%{q}%"
            contacts = conn.execute(
                """SELECT * FROM contacts
                   WHERE nom LIKE ? COLLATE NOCASE
                      OR email LIKE ? COLLATE NOCASE
                      OR telephone LIKE ?
                   ORDER BY nom COLLATE NOCASE""",
                (like, like, like)
            ).fetchall()
        else:
            contacts = conn.execute(
                "SELECT * FROM contacts ORDER BY nom COLLATE NOCASE"
            ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    contacts = [dict(c) for c in contacts]
    return render_template("index.html",
                           contacts=contacts,
                           total=total,
                           q=q,
                           user=session["user"])

@app.route("/contacts/add", methods=["GET", "POST"])
@login_required
def add_contact():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        telephone = request.form.get("telephone", "").strip()
        errors = validate_contact(nom, email, telephone)
        if errors:
            return render_template("form.html", mode="add", errors=errors,
                                   nom=nom, email=email, telephone=telephone,
                                   user=session["user"])
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO contacts (nom, email, telephone, date_ajout) VALUES (?, ?, ?, ?)",
                    (nom, email.lower(), telephone, now())
                )
            flash(f"Contact '{nom}' ajouté avec succès.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            errors = ["Email ou téléphone déjà utilisé."]
            return render_template("form.html", mode="add", errors=errors,
                                   nom=nom, email=email, telephone=telephone,
                                   user=session["user"])
    return render_template("form.html", mode="add", errors=[],
                           nom="", email="", telephone="",
                           user=session["user"])

@app.route("/contacts/edit/<int:contact_id>", methods=["GET", "POST"])
@login_required
def edit_contact(contact_id):
    with get_db() as conn:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
    if not contact:
        flash("Contact introuvable.", "error")
        return redirect(url_for("index"))
    contact = dict(contact)

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        telephone = request.form.get("telephone", "").strip()
        errors = validate_contact(nom, email, telephone)
        if errors:
            return render_template("form.html", mode="edit", errors=errors,
                                   contact=contact, nom=nom, email=email,
                                   telephone=telephone, user=session["user"])
        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE contacts SET nom=?, email=?, telephone=? WHERE id=?",
                    (nom, email.lower(), telephone, contact_id)
                )
            flash(f"Contact '{nom}' modifié.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            errors = ["Email ou téléphone déjà utilisé."]
            return render_template("form.html", mode="edit", errors=errors,
                                   contact=contact, nom=nom, email=email,
                                   telephone=telephone, user=session["user"])
    return render_template("form.html", mode="edit", errors=[],
                           contact=contact,
                           nom=contact["nom"], email=contact["email"],
                           telephone=contact["telephone"],
                           user=session["user"])

@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
@login_required
def delete_contact(contact_id):
    with get_db() as conn:
        row = conn.execute("SELECT nom FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row:
            conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            flash(f"Contact '{row['nom']}' supprimé.", "success")
        else:
            flash("Contact introuvable.", "error")
    return redirect(url_for("index"))

# ═══════════════════════════════════════════════
#  ROUTES — CSV
# ═══════════════════════════════════════════════

@app.route("/contacts/export")
@login_required
def export_csv():
    with get_db() as conn:
        contacts = conn.execute(
            "SELECT id, nom, email, telephone, date_ajout FROM contacts ORDER BY nom COLLATE NOCASE"
        ).fetchall()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "nom", "email", "telephone", "date_ajout"])
    writer.writeheader()
    for c in contacts:
        writer.writerow(dict(c))
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="contacts_export.csv"
    )

@app.route("/contacts/import", methods=["POST"])
@login_required
def import_csv():
    f = request.files.get("csv_file")
    if not f or not f.filename.endswith(".csv"):
        flash("Veuillez sélectionner un fichier CSV.", "error")
        return redirect(url_for("index"))
    imported = skipped = 0
    stream = io.StringIO(f.stream.read().decode("utf-8-sig"))
    reader = csv.DictReader(stream)
    for row in reader:
        nom = row.get("nom", "").strip()
        email = row.get("email", "").strip()
        telephone = row.get("telephone", "").strip()
        if nom and email and telephone:
            try:
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO contacts (nom, email, telephone, date_ajout) VALUES (?, ?, ?, ?)",
                        (nom, email.lower(), telephone, now())
                    )
                imported += 1
            except sqlite3.IntegrityError:
                skipped += 1
        else:
            skipped += 1
    msg = f"{imported} contact(s) importé(s)"
    if skipped:
        msg += f", {skipped} ignoré(s) (doublons/incomplets)"
    flash(msg, "success" if imported else "warning")
    return redirect(url_for("index"))

# ═══════════════════════════════════════════════
#  ROUTES — ADMIN PANEL
# ═══════════════════════════════════════════════

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin_panel():
    with get_db() as conn:
        admins = [r["username"] for r in conn.execute(
            "SELECT username FROM admins ORDER BY date_creation"
        ).fetchall()]
    return render_template("admin.html", admins=admins, user=session["user"])

@app.route("/admin/add", methods=["POST"])
@login_required
def admin_add():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    try:
        _validate_password(password)
        with get_db() as conn:
            conn.execute(
                "INSERT INTO admins (username, password_hash, date_creation) VALUES (?, ?, ?)",
                (username, _hash_password(password), now())
            )
        flash(f"Admin '{username}' ajouté.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except sqlite3.IntegrityError:
        flash("Ce nom d'utilisateur est déjà pris.", "error")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete/<username>", methods=["POST"])
@login_required
def admin_delete(username):
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
        if count <= 1:
            flash("Impossible de supprimer le dernier administrateur.", "error")
        else:
            conn.execute("DELETE FROM admins WHERE username = ?", (username,))
            flash(f"Admin '{username}' supprimé.", "success")
            if session["user"] == username:
                session.pop("user", None)
                return redirect(url_for("login"))
    return redirect(url_for("admin_panel"))

@app.route("/admin/change-password", methods=["POST"])
@login_required
def change_password():
    old_pw = request.form.get("old_password", "")
    new_pw = request.form.get("new_password", "")
    with get_db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM admins WHERE username = ?", (session["user"],)
        ).fetchone()
    if not row or not _verify_password(old_pw, row["password_hash"]):
        flash("Ancien mot de passe incorrect.", "error")
        return redirect(url_for("admin_panel"))
    try:
        _validate_password(new_pw)
        with get_db() as conn:
            conn.execute(
                "UPDATE admins SET password_hash = ? WHERE username = ?",
                (_hash_password(new_pw), session["user"])
            )
        flash("Mot de passe modifié avec succès.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("admin_panel"))

# ═══════════════════════════════════════════════
#  COMMUNICATION MODULE
# ═══════════════════════════════════════════════

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#SMTP
SMTP_HOST     = "smtp.gmail.com"          # smtp.office365.com for Outlook
SMTP_PORT     = 587                       # 587=STARTTLS | 465=SSL
SMTP_USER     = "aababou19@gmail.com"   # ← your sender email
SMTP_PASSWORD = "ufoj hvvn nger mdzg"     # ← your Gmail App Password
SMTP_NAME     = "AHMED AMIN Contacts"         # display name for recipients

#WHATSAPP
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # from twilio.com/console
TWILIO_AUTH_TOKEN  = "your_auth_token_here"               # from twilio.com/console
TWILIO_WA_FROM     = "whatsapp:+14155238886"              # sandbox number

# ── Message templates ────────────────────────────────────────────────────

TEMPLATES = {
    "rdv_confirmation": {
        "label": "Confirmation de rendez-vous",
        "icon": "📅",
        "subject": "Confirmation de votre rendez-vous",
        "body": """Bonjour {nom},

Nous vous confirmons votre rendez-vous prévu le {date} à {heure}.

Veuillez vous présenter 10 minutes avant l'heure prévue et munissez-vous de votre carte d'identité et de votre carte vitale.

En cas d'empêchement, merci de nous contacter au plus tôt afin d'annuler ou reporter votre rendez-vous.

Cordialement,
Le cabinet médical""",
    },
    "rdv_rappel": {
        "label": "Rappel de rendez-vous",
        "icon": "🔔",
        "subject": "Rappel : votre rendez-vous de demain",
        "body": """Bonjour {nom},

Ceci est un rappel concernant votre rendez-vous prévu demain le {date} à {heure}.

N'oubliez pas d'apporter vos documents médicaux et ordonnances en cours.

Cordialement,
Le cabinet médical""",
    },
    "resultats_labo": {
        "label": "Demande de résultats (laboratoire)",
        "icon": "🧪",
        "subject": "Demande de résultats d'analyses",
        "body": """Bonjour,

Nous vous contactons concernant les résultats d'analyses du patient : {nom}.

Pourriez-vous nous transmettre les résultats dans les meilleurs délais à l'adresse email suivante ou par fax ?

Merci de votre collaboration.

Cordialement,
Le cabinet médical""",
    },
    "prescription": {
        "label": "Envoi d'ordonnance",
        "icon": "💊",
        "subject": "Votre ordonnance médicale",
        "body": """Bonjour {nom},

Veuillez trouver ci-joint votre ordonnance médicale.

Cette ordonnance est valable 3 mois à compter de la date d'émission. Présentez-la à votre pharmacien pour obtenir vos médicaments.

En cas de questions, n'hésitez pas à nous contacter.

Cordialement,
Dr. {medecin}""",
    },
    "suivi": {
        "label": "Message de suivi patient",
        "icon": "💬",
        "subject": "Suivi de votre état de santé",
        "body": """Bonjour {nom},

Nous prenons de vos nouvelles suite à votre dernière consultation.

Comment vous sentez-vous ? Si vous avez des questions ou des préoccupations concernant votre traitement, n'hésitez pas à nous répondre ou à nous appeler.

Cordialement,
Le cabinet médical""",
    },
    "libre": {
        "label": "Message libre",
        "icon": "✏️",
        "subject": "",
        "body": "",
    },
}

# ── Routes ───────────────────────────────────────────────────────────────

@app.route("/contacts/<int:contact_id>/communicate", methods=["GET"])
@login_required
def communicate(contact_id):
    with get_db() as conn:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
    if not contact:
        flash("Contact introuvable.", "error")
        return redirect(url_for("index"))
    contact = dict(contact)
    return render_template("communicate.html",
                           contact=contact,
                           templates=TEMPLATES,
                           sender=SMTP_USER,
                           user=session["user"])


@app.route("/contacts/<int:contact_id>/send-email", methods=["POST"])
@login_required
def send_email(contact_id):
    with get_db() as conn:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
    if not contact:
        flash("Contact introuvable.", "error")
        return redirect(url_for("index"))
    contact = dict(contact)

    subject = request.form.get("subject", "").strip()
    body    = request.form.get("body", "").strip()

    if not subject or not body:
        flash("Veuillez remplir l'objet et le message.", "error")
        return redirect(url_for("communicate", contact_id=contact_id))

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SMTP_NAME} <{SMTP_USER}>"
        msg["To"]      = contact["email"]
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, contact["email"], msg.as_string())

        _log_message(contact_id, "email", subject, body)
        flash(f"✓ Email envoyé à {contact['nom']} ({contact['email']}).", "success")
    # except smtplib.SMTPAuthenticationError:
    #     flash("Échec SMTP : identifiants incorrects. Vérifiez SMTP_USER / SMTP_PASSWORD dans app.py.", "error")
    # except smtplib.SMTPException as e:
    #     flash(f"Erreur SMTP : {e}", "error")
    # except Exception as e:
    #     flash(f"Erreur : {e}", "error")

    except smtplib.SMTPAuthenticationError as e:
        flash(f"Échec SMTP : {e.smtp_code} — {e.smtp_error.decode()}", "error")
    except smtplib.SMTPException as e:
        flash(f"Erreur SMTP : {type(e).__name__} — {e}", "error")
    except Exception as e:
        flash(f"Erreur inattendue : {type(e).__name__} — {e}", "error")

    return redirect(url_for("communicate", contact_id=contact_id))


@app.route("/contacts/<int:contact_id>/send-whatsapp", methods=["POST"])
@login_required
def send_whatsapp(contact_id):
    with get_db() as conn:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
    if not contact:
        flash("Contact introuvable.", "error")
        return redirect(url_for("index"))
    contact = dict(contact)

    body    = request.form.get("body", "").strip()
    subject = request.form.get("subject", "Message WhatsApp").strip()

    if not body:
        flash("Le message ne peut pas être vide.", "error")
        return redirect(url_for("communicate", contact_id=contact_id))

    # Format phone: French 06/07 → +2126/+2127
    phone = re.sub(r"\D", "", contact["telephone"])
    if phone.startswith("0"):
        phone = "212" + phone[1:]

    text = f"Bonjour, je suis le cabinet médical.\n\n{body}"
    wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(text)}"

    _log_message(contact_id, "whatsapp", subject, body)

    # Pass the URL to the template to open it in a new tab via JS
    return render_template("communicate.html",
                           contact=contact,
                           templates=TEMPLATES,
                           sender=SMTP_USER,
                           user=session["user"],
                           wa_url=wa_url,
                           active_tab="whatsapp")
# ── Message log ──────────────────────────────────────────────────────────

def _init_messages_table():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id  INTEGER NOT NULL,
                type        TEXT NOT NULL,
                subject     TEXT,
                body        TEXT,
                sent_at     TEXT NOT NULL,
                FOREIGN KEY(contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)

def _log_message(contact_id, msg_type, subject, body):
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO messages (contact_id, type, subject, body, sent_at) VALUES (?, ?, ?, ?, ?)",
                (contact_id, msg_type, subject, body, now())
            )
    except Exception:
        pass  # logging failure should never break the flow

@app.route("/contacts/<int:contact_id>/history")
@login_required
def message_history(contact_id):
    with get_db() as conn:
        contact = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        messages = conn.execute(
            "SELECT * FROM messages WHERE contact_id = ? ORDER BY sent_at DESC",
            (contact_id,)
        ).fetchall()
    if not contact:
        flash("Contact introuvable.", "error")
        return redirect(url_for("index"))
    return render_template("history.html",
                           contact=dict(contact),
                           messages=[dict(m) for m in messages],
                           user=session["user"])


# ═══════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    _init_messages_table()
    app.run(debug=True, port=5000)
