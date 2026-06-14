# address_book — Flask Web App

Application web de gestion de contacts développée avec Flask + SQLite3.

## Structure

```
flask_app/
├── app.py              # Application principale Flask
├── contacts.db         # Base SQLite (créée automatiquement)
├── README.md
└── templates/
    ├── base.html       # Layout commun (nav, flash messages)
    ├── login.html      # Page de connexion
    ├── index.html      # Liste des contacts + détails + CSV
    ├── form.html       # Formulaire ajout / modification
    └── admin.html      # Panneau administrateur
```

## Installation & lancement

```bash
# 1. Installer Flask (bcrypt non requis)
pip install flask

# 2. Lancer l'application
python app.py

# 3. Ouvrir dans le navigateur
http://127.0.0.1:5000
```

## Compte par défaut

| Identifiant | Mot de passe |
|-------------|-------------|
| admin       | Admin1234!  |

## Fonctionnalités

- **Authentification** : login/logout avec hachage PBKDF2-SHA256
- **Contacts** : ajout, modification, suppression, recherche en temps réel
- **Panneau détails** : cliquez sur un contact pour voir ses infos inline
- **CSV** : export et import de contacts
- **Admin** : gestion des comptes administrateurs, changement de mot de passe

## Politique de mot de passe

≥ 8 caractères · 1 majuscule · 1 chiffre · 1 caractère spécial

## Base de données

La base `contacts.db` est partagée avec l'application Tkinter.
Elle est créée automatiquement au premier lancement avec un admin par défaut.








ydata-profiling==4.17.0
zipp==3.23.0
