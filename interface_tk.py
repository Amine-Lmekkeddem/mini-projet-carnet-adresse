"""
interface_tk.py — Application Carnet d'adresses (SQLite edition)
Dépendances : database.py · auth.py · login_window.py
              pip install bcrypt
"""

import tkinter as tk
from tkinter import filedialog
import re
import os

from database import (
    contact_ajouter, contact_tous, contact_rechercher,
    contact_modifier, contact_supprimer, contact_compter,
    exporter_csv, importer_csv,
)
from login_window import LoginWindow, AdminPanel

# ── Palette ────────────────────────────────────────────────────────────────
BG      = "#f8f5ff"
PANEL   = "#ede8fa"
CARD    = "#ffffff"
BORDER  = "#d0c0f0"
ACCENT  = "#7c3aed"
ACCENT2 = "#a855f7"
ACCENT3 = "#6d28d9"
TEXT    = "#1e0a3c"
MUTED   = "#9c7cc0"
MONO    = "Courier"
RED     = "#ff4d6d"
GREEN   = "#22c55e"


# ── Dialogs ────────────────────────────────────────────────────────────────

def styled_dialog(parent, kind, title, message):
    colors = {"error": RED, "warning": ACCENT2, "info": ACCENT, "success": GREEN}
    icons  = {"error": "✕", "warning": "⚠",    "info": "✓",    "success": "✓"}
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
    cv.create_rectangle(0, 0, 339, 40,  fill=color, outline="")
    tk.Label(win, text=f"{icon}  {title}", font=(MONO, 10, "bold"),
             fg=CARD, bg=color).place(x=14, y=10)
    tk.Label(win, text=message, font=(MONO, 10), fg=TEXT, bg=PANEL,
             wraplength=290, justify="center").place(x=25, y=60, width=290)
    tk.Button(win, text="OK", font=(MONO, 10, "bold"),
              bg=color, fg=CARD, relief="flat", bd=0,
              padx=30, pady=6, cursor="hand2",
              command=win.destroy).place(relx=0.5, y=135, anchor="n")
    parent.wait_window(win)


def styled_confirm(parent, title, message):
    result = [False]
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("340x190")
    win.resizable(False, False)
    win.configure(bg=PANEL)
    win.grab_set()

    cv = tk.Canvas(win, width=340, height=190, bg=PANEL, highlightthickness=0)
    cv.place(x=0, y=0)
    cv.create_rectangle(0, 0, 339, 189, outline=ACCENT2, width=2)
    cv.create_rectangle(0, 0, 339, 40,  fill=ACCENT2, outline="")
    tk.Label(win, text=f"⚠  {title}", font=(MONO, 10, "bold"),
             fg=CARD, bg=ACCENT2).place(x=14, y=10)
    tk.Label(win, text=message, font=(MONO, 10), fg=TEXT, bg=PANEL,
             wraplength=290, justify="center").place(x=25, y=58, width=290)

    def oui():
        result[0] = True
        win.destroy()

    tk.Button(win, text="Oui", font=(MONO, 10, "bold"),
              bg=ACCENT2, fg=CARD, relief="flat", bd=0,
              padx=26, pady=7, cursor="hand2", command=oui).place(x=80, y=135)
    tk.Button(win, text="Non", font=(MONO, 10, "bold"),
              bg=PANEL, fg=ACCENT2, relief="flat", bd=0,
              highlightthickness=1, highlightbackground=ACCENT2,
              padx=26, pady=7, cursor="hand2", command=win.destroy).place(x=185, y=135)

    parent.wait_window(win)
    return result[0]


# ════════════════════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self, current_user: str = "admin"):
        super().__init__()
        self._current_user = current_user
        self._contacts_cache: list[dict] = []     # contacts affichés
        self.title("contacts.db")
        self.geometry("615x715")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._build_ui()
        self._refresh_list()

    # ── Construction UI ──────────────────────────────────────────────────

    def _build_ui(self):
        # ── HEADER ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, pady=18)
        header.pack(fill=tk.X, padx=30)

        left = tk.Frame(header, bg=BG)
        left.pack(side=tk.LEFT)
        tk.Label(left, text="[ SQLite ]", font=(MONO, 9), fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(left, text="address_book", font=(MONO, 22, "bold"), fg=TEXT, bg=BG).pack(anchor="w")

        right = tk.Frame(header, bg=BG)
        right.pack(side=tk.RIGHT, anchor="e")
        self.counter_var = tk.StringVar(value="0 contacts")
        tk.Label(right, textvariable=self.counter_var,
                 font=(MONO, 9), fg=MUTED, bg=BG).pack(anchor="e")
        badge = tk.Frame(right, bg=ACCENT3, padx=8, pady=2)
        badge.pack(anchor="e", pady=(5, 0))
        tk.Label(badge, text=f"★ {self._current_user}",
                 font=(MONO, 8, "bold"), fg=CARD, bg=ACCENT3).pack()

        # séparateur
        self._sep_line(ACCENT)

        # ── PANNEAU DÉTAILS ──────────────────────────────────────────────
        detail_outer = tk.Frame(self, bg=BG, padx=30, pady=10)
        detail_outer.pack(fill=tk.X)

        detail_border = tk.Frame(detail_outer, bg=BORDER, padx=1, pady=1)
        detail_border.pack(fill=tk.X)

        self._detail_panel = tk.Frame(detail_border, bg=PANEL, padx=16, pady=12)
        self._detail_panel.pack(fill=tk.X)

        # placeholder label shown when nothing is selected
        self._detail_placeholder = tk.Label(
            self._detail_panel,
            text="← click a contact to see details",
            font=(MONO, 9), fg=MUTED, bg=PANEL
        )
        self._detail_placeholder.pack(anchor="w")

        # labels for actual contact info (hidden until a contact is selected)
        self._detail_name  = tk.Label(self._detail_panel, text="", font=(MONO, 13, "bold"), fg=ACCENT,  bg=PANEL)
        self._detail_email = tk.Label(self._detail_panel, text="", font=(MONO, 9),           fg=TEXT,    bg=PANEL)
        self._detail_tel   = tk.Label(self._detail_panel, text="", font=(MONO, 9),           fg=TEXT,    bg=PANEL)
        self._detail_date  = tk.Label(self._detail_panel, text="", font=(MONO, 8),           fg=MUTED,   bg=PANEL)

        self._sep_line(BORDER)

        # ── BARRE DE RECHERCHE ───────────────────────────────────────────
        search_frame = tk.Frame(self, bg=BG, padx=30, pady=10)
        search_frame.pack(fill=tk.X)

        tk.Label(search_frame, text="⌕", font=(MONO, 13),
                 fg=MUTED, bg=BG).pack(side=tk.LEFT, padx=(0, 6))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        search_entry = tk.Entry(
            search_frame, textvariable=self._search_var,
            font=(MONO, 11), bg=CARD, fg=TEXT,
            insertbackground=ACCENT, relief="flat",
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT, bd=0
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)

        tk.Button(search_frame, text="✕", font=(MONO, 10), bg=BG, fg=MUTED,
                  relief="flat", bd=0, cursor="hand2",
                  command=lambda: self._search_var.set("")).pack(side=tk.LEFT, padx=(6, 0))

        # ── LISTBOX ──────────────────────────────────────────────────────
        mid = tk.Frame(self, bg=BG, padx=30)
        mid.pack(fill=tk.X)

        self._list_label_var = tk.StringVar(value="─── contacts ───────────────────────────────")
        tk.Label(mid, textvariable=self._list_label_var,
                 font=(MONO, 8), fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 5))

        lw = tk.Frame(mid, bg=ACCENT, padx=1, pady=1)
        lw.pack(fill=tk.X)
        inner = tk.Frame(lw, bg=CARD)
        inner.pack(fill=tk.X)

        sb = tk.Scrollbar(inner, troughcolor=CARD, bg=BORDER,
                          activebackground=MUTED, bd=0, width=8)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            inner, yscrollcommand=sb.set, font=(MONO, 11),
            bg=CARD, fg=TEXT,
            selectbackground=ACCENT, selectforeground=CARD,
            activestyle="none", borderwidth=0, highlightthickness=0,
            relief="flat", height=12, cursor="hand2"
        )
        self.listbox.pack(fill=tk.X, padx=10, pady=8)
        sb.config(command=self.listbox.yview)
        self.listbox.bind("<ButtonRelease-1>", lambda e: self._afficher_details())
        self.listbox.bind("<Double-Button-1>", lambda e: self._afficher_details())

        # ── BOUTONS CONTACTS ─────────────────────────────────────────────
        self._sep_line(BORDER)

        bot = tk.Frame(self, bg=BG, pady=12, padx=30)
        bot.pack(fill=tk.X)

        contact_btns = [
            ("+ add",    ACCENT,  self._form_ajout),
            ("~ edit",   ACCENT3, self._form_modifier),
            ("- delete", ACCENT2, self._supprimer),
        ]
        for label, color, cmd in contact_btns:
            b = tk.Button(bot, text=label, font=(MONO, 9, "bold"),
                          bg=BG, fg=color,
                          activebackground=color, activeforeground=CARD,
                          relief="flat", bd=0, padx=14, pady=9,
                          cursor="hand2", command=cmd,
                          highlightthickness=1, highlightbackground=color)
            b.pack(side=tk.LEFT, padx=(0, 8))
            self._add_hover(b, color)

        ref = tk.Button(bot, text="↺", font=(MONO, 13), bg=BG, fg=MUTED,
                        activebackground=BG, activeforeground=TEXT,
                        relief="flat", bd=0, cursor="hand2",
                        highlightthickness=0, command=self._refresh_list)
        ref.pack(side=tk.RIGHT)

        # ── BARRE CSV ────────────────────────────────────────────────────
        self._sep_line(BORDER)

        csv_bar = tk.Frame(self, bg=BG, pady=8, padx=30)
        csv_bar.pack(fill=tk.X)

        tk.Label(csv_bar, text="CSV :", font=(MONO, 8), fg=MUTED, bg=BG).pack(side=tk.LEFT)

        csv_btns = [
            ("↓ exporter", GREEN,   self._exporter_csv),
            ("↑ importer", ACCENT2, self._importer_csv),
        ]
        for label, color, cmd in csv_btns:
            b = tk.Button(csv_bar, text=label, font=(MONO, 9, "bold"),
                          bg=BG, fg=color,
                          activebackground=color, activeforeground=CARD,
                          relief="flat", bd=0, padx=14, pady=7,
                          cursor="hand2", command=cmd,
                          highlightthickness=1, highlightbackground=color)
            b.pack(side=tk.LEFT, padx=(8, 0))
            self._add_hover(b, color)

        # ── BARRE ADMIN ──────────────────────────────────────────────────
        self._sep_line(BORDER)

        admin_bar = tk.Frame(self, bg=BG, pady=8, padx=30)
        admin_bar.pack(fill=tk.X)

        self._make_bar_btn(admin_bar, "⚙ admin",      MUTED,  ACCENT3, self._ouvrir_admin_panel, "left")
        self._make_bar_btn(admin_bar, "⏻ déconnexion", MUTED,  RED,     self._logout,             "right")

    # ── Helpers visuels ──────────────────────────────────────────────────

    def _sep_line(self, color):
        cv = tk.Canvas(self, height=1, bg=BG, highlightthickness=0)
        cv.pack(fill=tk.X, padx=30)
        cv.create_line(0, 0, 700, 0, fill=color, width=1)

    def _add_hover(self, btn, color):
        btn.bind("<Enter>", lambda e: btn.config(bg=color, fg=CARD))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG, fg=color))

    def _make_bar_btn(self, parent, text, fg_color, hover_color, cmd, side):
        b = tk.Button(parent, text=text, font=(MONO, 9, "bold"),
                      bg=BG, fg=fg_color,
                      activebackground=hover_color, activeforeground=CARD,
                      relief="flat", bd=0, padx=14, pady=6,
                      cursor="hand2", command=cmd,
                      highlightthickness=1, highlightbackground=BORDER)
        b.pack(side=side)
        b.bind("<Enter>", lambda e: b.config(bg=hover_color, fg=CARD))
        b.bind("<Leave>", lambda e: b.config(bg=BG, fg=fg_color))

    # ── Données ──────────────────────────────────────────────────────────

    def _refresh_list(self, contacts: list[dict] | None = None):
        if contacts is None:
            contacts = contact_tous()
        self._contacts_cache = contacts
        self.listbox.delete(0, tk.END)
        # reset detail panel
        for lbl in (self._detail_name, self._detail_email, self._detail_tel, self._detail_date):
            lbl.pack_forget()
        self._detail_placeholder.pack(anchor="w")
        for c in contacts:
            self.listbox.insert(tk.END, f"  {c['nom']:<24} {c['telephone']}")
        n = len(contacts)
        total = contact_compter()
        if n == total:
            self.counter_var.set(f"{total} contact{'s' if total != 1 else ''}")
            self._list_label_var.set("─── contacts ───────────────────────────────")
        else:
            self.counter_var.set(f"{n} / {total} trouvés")
            self._list_label_var.set(f"─── résultats de recherche ({n}) ──────────────")

    def _on_search(self):
        terme = self._search_var.get().strip()
        if terme:
            self._refresh_list(contact_rechercher(terme))
        else:
            self._refresh_list()

    def _selected(self) -> dict | None:
        sel = self.listbox.curselection()
        if not sel:
            styled_dialog(self, "warning", "Sélection", "Veuillez sélectionner un contact.")
            return None
        return self._contacts_cache[sel[0]]

    # ── Actions contacts ─────────────────────────────────────────────────

    def _afficher_details(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        c = self._contacts_cache[sel[0]]

        # hide placeholder, show detail labels
        self._detail_placeholder.pack_forget()
        self._detail_name.config(text=f"  {c['nom']}")
        self._detail_email.config(text=f"  \u2709  {c['email']}")
        self._detail_tel.config(text=f"  \u260e  {c['telephone']}")
        self._detail_date.config(text=f"  ajout\u00e9 le {c['date_ajout']}")

        for lbl in (self._detail_name, self._detail_email, self._detail_tel, self._detail_date):
            lbl.pack(anchor="w", pady=(2, 0))

    def _supprimer(self):
        c = self._selected()
        if not c:
            return
        if styled_confirm(self, "Confirmer", f"Supprimer '{c['nom']}' ?"):
            contact_supprimer(c["email"])
            self._refresh_list()

    # ── Formulaire ajout ─────────────────────────────────────────────────

    def _form_ajout(self):
        self._ouvrir_formulaire(mode="ajout")

    def _form_modifier(self):
        c = self._selected()
        if not c:
            return
        self._ouvrir_formulaire(mode="edition", contact=c)

    def _ouvrir_formulaire(self, mode: str = "ajout", contact: dict | None = None):
        is_edit = (mode == "edition")
        win = tk.Toplevel(self)
        win.title("Modifier le contact" if is_edit else "Nouveau contact")
        win.geometry("380x330")
        win.resizable(False, False)
        win.configure(bg=PANEL)
        win.grab_set()

        cv = tk.Canvas(win, width=380, height=330, bg=PANEL, highlightthickness=0)
        cv.place(x=0, y=0)
        cv.create_rectangle(0, 0, 379, 329, outline=ACCENT, width=2)
        cv.create_rectangle(0, 0, 379, 44,  fill=ACCENT, outline="")
        titre = "~ modifier" if is_edit else "+ nouveau contact"
        tk.Label(win, text=titre, font=(MONO, 10, "bold"),
                 fg=CARD, bg=ACCENT).place(x=14, y=12)

        form = tk.Frame(win, bg=PANEL, padx=28)
        form.place(x=0, y=54, width=380)

        entries = {}
        for key, label in [("nom", "Nom"), ("email", "Email"), ("telephone", "Téléphone")]:
            tk.Label(form, text=f"  {label}", font=(MONO, 8), fg=MUTED,
                     bg=PANEL, anchor="w").pack(fill=tk.X, pady=(9, 0))
            e = tk.Entry(form, font=(MONO, 11), bg=CARD, fg=TEXT,
                         insertbackground=ACCENT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, bd=0)
            e.pack(fill=tk.X, ipady=7)
            if is_edit and contact:
                e.insert(0, contact.get(key, ""))
            entries[key] = e

        def valider():
            nom       = entries["nom"].get().strip()
            email     = entries["email"].get().strip()
            telephone = entries["telephone"].get().strip()

            if not nom:
                styled_dialog(win, "error", "Erreur", "Le nom ne peut pas être vide."); return
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                styled_dialog(win, "error", "Erreur", "Email invalide.\nEx : exemple@mail.com"); return
            if not (telephone.isdigit() and len(telephone) == 10):
                styled_dialog(win, "error", "Erreur", "Le téléphone doit\ncontenir 10 chiffres."); return

            if is_edit:
                ok = contact_modifier(contact["email"], nom, email, telephone)
                if ok:
                    self._refresh_list(); win.destroy()
                else:
                    styled_dialog(win, "error", "Doublon", "Email ou téléphone\ndéjà utilisé.")
            else:
                ok = contact_ajouter(nom, email, telephone)
                if ok:
                    self._refresh_list(); win.destroy()
                else:
                    styled_dialog(win, "error", "Doublon", "Email ou téléphone\ndéjà utilisé.")

        lbl = "→ enregistrer" if is_edit else "→ ajouter"
        tk.Button(form, text=lbl, font=(MONO, 10, "bold"),
                  bg=ACCENT, fg=CARD, activebackground=ACCENT3, activeforeground=CARD,
                  relief="flat", bd=0, pady=9, cursor="hand2",
                  command=valider).pack(fill=tk.X, pady=(18, 0))

    # ── Export / Import CSV ──────────────────────────────────────────────

    def _exporter_csv(self):
        chemin = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter les contacts",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")],
            initialfile="contacts_export.csv",
        )
        if not chemin:
            return
        n = exporter_csv(chemin)
        if n > 0:
            styled_dialog(self, "success", "Export réussi",
                          f"{n} contact{'s' if n > 1 else ''} exporté{'s' if n > 1 else ''}\nvers :\n{os.path.basename(chemin)}")
        else:
            styled_dialog(self, "warning", "Export vide", "Aucun contact à exporter.")

    def _importer_csv(self):
        chemin = filedialog.askopenfilename(
            parent=self,
            title="Importer des contacts",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")],
        )
        if not chemin:
            return
        try:
            imported, skipped = importer_csv(chemin)
        except FileNotFoundError as e:
            styled_dialog(self, "error", "Erreur", str(e))
            return
        except Exception as e:
            styled_dialog(self, "error", "Erreur de lecture", str(e))
            return

        self._refresh_list()
        msg = f"{imported} importé{'s' if imported != 1 else ''}"
        if skipped:
            msg += f"\n{skipped} ignoré{'s' if skipped != 1 else ''} (doublons/incomplets)"
        styled_dialog(self, "success" if imported else "warning", "Import terminé", msg)

    # ── Admin / Auth ─────────────────────────────────────────────────────

    def _ouvrir_admin_panel(self):
        AdminPanel(self, self._current_user)

    def _logout(self):
        if styled_confirm(self, "Déconnexion", "Voulez-vous vous déconnecter ?"):
            self.destroy()
            LoginWindow(App).mainloop()


# ── Point d'entrée ────────────────────────────────────────────────────────
if __name__ == "__main__":
    LoginWindow(App).mainloop()