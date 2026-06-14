"""
login_window.py — Fenêtre de connexion et panneau d'administration
À importer dans interface_tk.py (voir instructions en bas de fichier).
"""

import tkinter as tk
import sys, os

# Permet d'importer auth.py depuis le même répertoire
sys.path.insert(0, os.path.dirname(__file__))
from auth import (
    authenticate, add_admin, delete_admin,
    change_password, list_admins, _validate_password
)

# ── Palette (identique à interface_tk.py) ───────────────────────────────────
BG     = "#f8f5ff"
PANEL  = "#ede8fa"
CARD   = "#ffffff"
BORDER = "#d0c0f0"
ACCENT = "#7c3aed"
ACCENT2 = "#a855f7"
ACCENT3 = "#6d28d9"
TEXT   = "#1e0a3c"
MUTED  = "#9c7cc0"
MONO   = "Courier"
RED    = "#ff4d6d"


# ── Helper : dialog stylisé (copie légère) ───────────────────────────────────

def _dialog(parent, kind, title, message):
    colors = {"error": RED, "warning": ACCENT2, "info": ACCENT, "success": "#22c55e"}
    icons  = {"error": "✕", "warning": "⚠", "info": "i", "success": "✓"}
    color  = colors.get(kind, ACCENT)
    icon   = icons.get(kind, "i")

    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("340x180")
    win.resizable(False, False)
    win.configure(bg=PANEL)
    win.grab_set()

    cv = tk.Canvas(win, width=340, height=180, bg=PANEL, highlightthickness=0)
    cv.place(x=0, y=0)
    cv.create_rectangle(0, 0, 339, 179, outline=color, width=2)
    cv.create_rectangle(0, 0, 339, 40, fill=color, outline="")
    tk.Label(win, text=f"{icon}  {title}", font=(MONO, 10, "bold"),
             fg=CARD, bg=color).place(x=14, y=10)
    tk.Label(win, text=message, font=(MONO, 10), fg=TEXT, bg=PANEL,
             wraplength=290, justify="center").place(x=25, y=60, width=290)
    tk.Button(win, text="OK", font=(MONO, 10, "bold"),
              bg=color, fg=CARD, relief="flat", bd=0,
              padx=30, pady=6, cursor="hand2",
              command=win.destroy).place(relx=0.5, y=135, anchor="n")
    parent.wait_window(win)


# ════════════════════════════════════════════════════════════════════════════
#  FENÊTRE DE CONNEXION
# ════════════════════════════════════════════════════════════════════════════

class LoginWindow(tk.Tk):
    """
    Fenêtre de connexion autonome.
    Lance App() si l'authentification réussit, se ferme sinon après 3 échecs.
    """

    MAX_ATTEMPTS = 3

    def __init__(self, app_class):
        super().__init__()
        self._app_class = app_class
        self._attempts  = 0
        self._locked    = False

        self.title("Connexion — contacts.db")
        self.geometry("420x420")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._build()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build(self):
        # En-tête
        cv = tk.Canvas(self, width=420, height=90, bg=ACCENT, highlightthickness=0)
        cv.pack(fill=tk.X)
        tk.Label(self, text="[ SECURE ACCESS ]", font=(MONO, 8),
                 fg=ACCENT2, bg=ACCENT).place(x=20, y=14)
        tk.Label(self, text="contacts.db", font=(MONO, 22, "bold"),
                 fg=CARD, bg=ACCENT).place(x=20, y=32)
        tk.Label(self, text="Espace administrateur", font=(MONO, 9),
                 fg=ACCENT2, bg=ACCENT).place(x=20, y=66)

        # Formulaire
        form = tk.Frame(self, bg=BG, padx=40)
        form.place(x=0, y=110, width=420)

        # Champ utilisateur
        tk.Label(form, text="  utilisateur", font=(MONO, 8),
                 fg=MUTED, bg=BG, anchor="w").pack(fill=tk.X, pady=(18, 0))
        self._user_entry = self._make_entry(form)

        # Champ mot de passe
        tk.Label(form, text="  mot de passe", font=(MONO, 8),
                 fg=MUTED, bg=BG, anchor="w").pack(fill=tk.X, pady=(14, 0))
        self._pass_entry = self._make_entry(form, show="•")

        # Tentatives restantes
        self._status_var = tk.StringVar(value="")
        tk.Label(form, textvariable=self._status_var, font=(MONO, 8),
                 fg=RED, bg=BG).pack(anchor="w", pady=(6, 0))

        # Bouton connexion
        self._btn = tk.Button(
            form, text="→ connexion", font=(MONO, 11, "bold"),
            bg=ACCENT, fg=CARD, activebackground=ACCENT3, activeforeground=CARD,
            relief="flat", bd=0, pady=11, cursor="hand2",
            command=self._login
        )
        self._btn.pack(fill=tk.X, pady=(14, 0))

        # Bind Enter
        self.bind("<Return>", lambda e: self._login())

       

    def _make_entry(self, parent, show=None):
        e = tk.Entry(parent, font=(MONO, 12), bg=CARD, fg=TEXT,
                     insertbackground=ACCENT, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, bd=0, show=show or "")
        e.pack(fill=tk.X, ipady=8)
        return e

    # ── Logique ─────────────────────────────────────────────────────────────

    def _login(self):
        if self._locked:
            return

        username = self._user_entry.get().strip()
        password = self._pass_entry.get()

        if not username or not password:
            self._status_var.set("Veuillez remplir tous les champs.")
            return

        if authenticate(username, password):
            self._launch_app()
        else:
            self._attempts += 1
            remaining = self.MAX_ATTEMPTS - self._attempts
            if remaining <= 0:
                self._locked = True
                self._btn.config(state="disabled", bg=MUTED)
                self._status_var.set("Compte verrouillé. Relancez l'application.")
            else:
                self._status_var.set(
                    f"Identifiants incorrects. {remaining} tentative(s) restante(s)."
                )
                self._pass_entry.delete(0, tk.END)

    def _launch_app(self):
        """Ferme la fenêtre de login et ouvre l'application principale."""
        self.destroy()
        app = self._app_class()
        app.mainloop()


# ════════════════════════════════════════════════════════════════════════════
#  PANNEAU D'ADMINISTRATION (gérer les comptes admins)
# ════════════════════════════════════════════════════════════════════════════

class AdminPanel(tk.Toplevel):
    """
    Panneau accessible depuis l'application principale pour gérer les admins.
    Instancier avec AdminPanel(parent, current_user).
    """

    def __init__(self, parent, current_user: str):
        super().__init__(parent)
        self._current = current_user
        self.title("Gestion des administrateurs")
        self.geometry("440x540")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self._build()
        self._refresh()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build(self):
        # Bandeau
        cv = tk.Canvas(self, width=440, height=48, bg=ACCENT3, highlightthickness=0)
        cv.pack(fill=tk.X)
        tk.Label(self, text="⚙  gestion des admins", font=(MONO, 11, "bold"),
                 fg=CARD, bg=ACCENT3).place(x=16, y=12)

        # Liste
        mid = tk.Frame(self, bg=BG, padx=24, pady=16)
        mid.pack(fill=tk.BOTH, expand=True)

        tk.Label(mid, text="─── comptes administrateurs ────────────────",
                 font=(MONO, 8), fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 6))

        lw = tk.Frame(mid, bg=ACCENT, padx=1, pady=1)
        lw.pack(fill=tk.X)
        inner = tk.Frame(lw, bg=CARD)
        inner.pack(fill=tk.X)

        self._listbox = tk.Listbox(
            inner, font=(MONO, 11), bg=CARD, fg=TEXT,
            selectbackground=ACCENT, selectforeground=CARD,
            activestyle="none", borderwidth=0, highlightthickness=0,
            relief="flat", height=6
        )
        self._listbox.pack(fill=tk.X, padx=10, pady=8)

        # Bouton supprimer
        tk.Button(mid, text="- supprimer le compte sélectionné",
                  font=(MONO, 9), bg=BG, fg=RED,
                  activebackground=RED, activeforeground=CARD,
                  relief="flat", bd=0, pady=6, cursor="hand2",
                  highlightthickness=1, highlightbackground=RED,
                  command=self._delete_admin).pack(fill=tk.X, pady=(8, 0))

        # Séparateur
        tk.Label(mid, text="─── ajouter un administrateur ───────────────",
                 font=(MONO, 8), fg=MUTED, bg=BG).pack(anchor="w", pady=(20, 6))

        for label, key in [("  nom d'utilisateur", "new_user"), ("  mot de passe", "new_pass")]:
            tk.Label(mid, text=label, font=(MONO, 8), fg=MUTED,
                     bg=BG, anchor="w").pack(fill=tk.X, pady=(6, 0))
            show = "•" if "pass" in key else ""
            e = tk.Entry(mid, font=(MONO, 11), bg=CARD, fg=TEXT,
                         insertbackground=ACCENT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, bd=0, show=show)
            e.pack(fill=tk.X, ipady=7)
            setattr(self, f"_{key}_entry", e)

        tk.Button(mid, text="→ créer le compte", font=(MONO, 10, "bold"),
                  bg=ACCENT, fg=CARD, activebackground=ACCENT3, activeforeground=CARD,
                  relief="flat", bd=0, pady=8, cursor="hand2",
                  command=self._add_admin).pack(fill=tk.X, pady=(10, 0))

        # Séparateur
        tk.Label(mid, text="─── changer mon mot de passe ────────────────",
                 font=(MONO, 8), fg=MUTED, bg=BG).pack(anchor="w", pady=(20, 6))

        tk.Button(mid, text="~ modifier mon mot de passe", font=(MONO, 9),
                  bg=BG, fg=ACCENT2,
                  activebackground=ACCENT2, activeforeground=CARD,
                  relief="flat", bd=0, pady=6, cursor="hand2",
                  highlightthickness=1, highlightbackground=ACCENT2,
                  command=self._change_password_dialog).pack(fill=tk.X)

    # ── Données ─────────────────────────────────────────────────────────────

    def _refresh(self):
        self._listbox.delete(0, tk.END)
        for name in list_admins():
            marker = "  ★ " if name == self._current else "    "
            self._listbox.insert(tk.END, f"{marker}{name}")

    def _add_admin(self):
        username = self._new_user_entry.get().strip()
        password = self._new_pass_entry.get()
        if not username or not password:
            _dialog(self, "error", "Erreur", "Remplissez tous les champs.")
            return
        try:
            created = add_admin(username, password)
        except ValueError as e:
            _dialog(self, "error", "Politique de MDP", str(e))
            return
        if created:
            self._new_user_entry.delete(0, tk.END)
            self._new_pass_entry.delete(0, tk.END)
            _dialog(self, "success", "Succès", f"Compte '{username}' créé.")
            self._refresh()
        else:
            _dialog(self, "warning", "Doublon", f"'{username}' existe déjà.")

    def _delete_admin(self):
        sel = self._listbox.curselection()
        if not sel:
            _dialog(self, "warning", "Sélection", "Sélectionnez un compte.")
            return
        name = list_admins()[sel[0]]
        if name == self._current:
            _dialog(self, "error", "Interdit", "Vous ne pouvez pas\nsupprimer votre propre compte.")
            return
        try:
            delete_admin(name)
            _dialog(self, "info", "Supprimé", f"Compte '{name}' supprimé.")
            self._refresh()
        except ValueError as e:
            _dialog(self, "error", "Erreur", str(e))

    def _change_password_dialog(self):
        ChangePasswordDialog(self, self._current)


# ════════════════════════════════════════════════════════════════════════════
#  DIALOGUE CHANGEMENT DE MOT DE PASSE
# ════════════════════════════════════════════════════════════════════════════

class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent, username: str):
        super().__init__(parent)
        self._username = username
        self.title("Changer le mot de passe")
        self.geometry("380x340")
        self.resizable(False, False)
        self.configure(bg=PANEL)
        self.grab_set()
        self._build()

    def _build(self):
        cv = tk.Canvas(self, width=380, height=44, bg=ACCENT2, highlightthickness=0)
        cv.pack(fill=tk.X)
        tk.Label(self, text="~ changer le mot de passe", font=(MONO, 10, "bold"),
                 fg=CARD, bg=ACCENT2).place(x=14, y=11)

        form = tk.Frame(self, bg=PANEL, padx=28)
        form.place(x=0, y=54, width=380)

        labels = [
            ("  ancien mot de passe", "_old"),
            ("  nouveau mot de passe", "_new1"),
            ("  confirmer le nouveau", "_new2"),
        ]
        for label, attr in labels:
            tk.Label(form, text=label, font=(MONO, 8), fg=MUTED,
                     bg=PANEL, anchor="w").pack(fill=tk.X, pady=(10, 0))
            e = tk.Entry(form, show="•", font=(MONO, 11), bg=CARD, fg=TEXT,
                         insertbackground=ACCENT2, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT2, bd=0)
            e.pack(fill=tk.X, ipady=7)
            setattr(self, f"{attr}_entry", e)

        tk.Button(form, text="→ valider", font=(MONO, 10, "bold"),
                  bg=ACCENT2, fg=CARD, activebackground=ACCENT3, activeforeground=CARD,
                  relief="flat", bd=0, pady=9, cursor="hand2",
                  command=self._submit).pack(fill=tk.X, pady=(18, 0))

    def _submit(self):
        old  = self._old_entry.get()
        new1 = self._new1_entry.get()
        new2 = self._new2_entry.get()

        if new1 != new2:
            _dialog(self, "error", "Erreur", "Les nouveaux mots de passe\nne correspondent pas.")
            return
        try:
            _validate_password(new1)
        except ValueError as e:
            _dialog(self, "error", "Politique", str(e))
            return
        if change_password(self._username, old, new1):
            _dialog(self, "success", "Succès", "Mot de passe modifié.")
            self.destroy()
        else:
            _dialog(self, "error", "Erreur", "Ancien mot de passe incorrect.")