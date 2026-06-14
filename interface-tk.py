import tkinter as tk
import re
import sys

sys.path.insert(0, '/mnt/user-data/uploads')
from address_book import AddressBook

# ── Palette ────────────────────────────────────────────────────────────────
BG        = "#f8f5ff"
PANEL     = "#ede8fa"
CARD      = "#ffffff"
BORDER    = "#d0c0f0"
ACCENT    = "#7c3aed"
ACCENT2   = "#a855f7"
ACCENT3   = "#6d28d9"
TEXT      = "#1e0a3c"
MUTED     = "#9c7cc0"
MONO      = "Courier"


def styled_dialog(parent, kind, title, message):
    """Boîte de dialogue custom stylisée (info / warning / error)."""
    colors = {
        "error":   ("#ff4d6d", "✕"),
        "warning": (ACCENT2,   "⚠"),
        "info":    (ACCENT,    "✓"),
    }
    color, icon = colors.get(kind, (ACCENT, "i"))

    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("340x180")
    win.resizable(False, False)
    win.configure(bg=PANEL)
    win.grab_set()

    # bordure colorée
    cv = tk.Canvas(win, width=340, height=180, bg=PANEL, highlightthickness=0)
    cv.place(x=0, y=0)
    cv.create_rectangle(0, 0, 339, 179, outline=color, width=2)
    # bande supérieure
    cv.create_rectangle(0, 0, 339, 40, fill=color, outline="")

    tk.Label(win, text=f"{icon}  {title}", font=(MONO, 10, "bold"),
             fg=CARD, bg=color).place(x=14, y=10)

    tk.Label(win, text=message, font=(MONO, 10), fg=TEXT, bg=PANEL,
             wraplength=290, justify="center").place(x=25, y=60, width=290)

    tk.Button(win, text="OK", font=(MONO, 10, "bold"),
              bg=color, fg=CARD, activebackground=TEXT, activeforeground=CARD,
              relief="flat", bd=0, padx=30, pady=6, cursor="hand2",
              command=win.destroy).place(relx=0.5, y=135, anchor="n")

    parent.wait_window(win)


def styled_confirm(parent, title, message):
    """Boîte de confirmation custom — retourne True si oui."""
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
    cv.create_rectangle(0, 0, 339, 40, fill=ACCENT2, outline="")

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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("contacts.db")
        self.geometry("560x560")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.carnet = AddressBook()
        self._build_ui()
        self._refresh_list()

    # ── UI principale ───────────────────────────────────────────────────────

    def _build_ui(self):
        # HEADER
        header = tk.Frame(self, bg=BG, pady=22)
        header.pack(fill=tk.X, padx=30)

        left = tk.Frame(header, bg=BG)
        left.pack(side=tk.LEFT)
        tk.Label(left, text="[ CARNET ]", font=(MONO, 9), fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(left, text="address_book", font=(MONO, 22, "bold"), fg=TEXT, bg=BG).pack(anchor="w")

        self.counter_var = tk.StringVar(value="0 contacts")
        tk.Label(header, textvariable=self.counter_var, font=(MONO, 9),
                 fg=MUTED, bg=BG).pack(side=tk.RIGHT, anchor="se", pady=(18, 0))

        sep = tk.Canvas(self, height=1, bg=BG, highlightthickness=0)
        sep.pack(fill=tk.X, padx=30)
        sep.create_line(0, 0, 600, 0, fill=ACCENT, width=1)

        # LISTBOX
        mid = tk.Frame(self, bg=BG, padx=30, pady=18)
        mid.pack(fill=tk.BOTH, expand=True)

        tk.Label(mid, text="─── contacts ───────────────────────────────",
                 font=(MONO, 8), fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 6))

        list_wrap = tk.Frame(mid, bg=ACCENT, padx=1, pady=1)
        list_wrap.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(list_wrap, bg=CARD)
        inner.pack(fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(inner, troughcolor=CARD, bg=BORDER,
                          activebackground=MUTED, bd=0, width=8)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            inner, yscrollcommand=sb.set, font=(MONO, 11),
            bg=CARD, fg=TEXT,
            selectbackground=ACCENT, selectforeground=CARD,
            activestyle="none", borderwidth=0, highlightthickness=0,
            relief="flat", height=13, cursor="hand2"
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        sb.config(command=self.listbox.yview)
        self.listbox.bind("<Double-Button-1>", lambda e: self._afficher_details())

        # BOUTONS
        sep2 = tk.Canvas(self, height=1, bg=BG, highlightthickness=0)
        sep2.pack(fill=tk.X, padx=30)
        sep2.create_line(0, 0, 600, 0, fill=BORDER, width=1)

        bot = tk.Frame(self, bg=BG, pady=18, padx=30)
        bot.pack(fill=tk.X)

        btns = [
            ("+ add",    ACCENT,  self._ouvrir_formulaire_ajout),
            ("- delete", ACCENT2, self._supprimer_contact),
            ("~ info",   ACCENT3, self._afficher_details),
        ]
        for label, color, cmd in btns:
            b = tk.Button(
                bot, text=label, font=(MONO, 10, "bold"),
                bg=BG, fg=color,
                activebackground=color, activeforeground=CARD,
                relief="flat", bd=0, padx=18, pady=10,
                cursor="hand2", command=cmd,
                highlightthickness=1, highlightbackground=color
            )
            b.pack(side=tk.LEFT, padx=(0, 12))
            self._add_hover(b, color)

        ref = tk.Button(bot, text="recharger", font=(MONO, 13), bg=BG, fg=MUTED,
                        activebackground=BG, activeforeground=TEXT,
                        relief="flat", bd=0, cursor="hand2",
                        highlightthickness=0, command=self._refresh_list)
        ref.pack(side=tk.RIGHT)

    def _add_hover(self, btn, color):
        btn.bind("<Enter>", lambda e: btn.config(bg=color, fg=CARD))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG, fg=color))

    # ── Données ─────────────────────────────────────────────────────────────

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        contacts = sorted(self.carnet.get_all_contacts(), key=lambda c: c.nom.lower())
        for c in contacts:
            self.listbox.insert(tk.END, f"  {c.nom:<22}  {c.telephone}")
        self.counter_var.set(f"{len(contacts)} contact{'s' if len(contacts) != 1 else ''}")

    def _get_selected_contact(self):
        sel = self.listbox.curselection()
        if not sel:
            styled_dialog(self, "warning", "Sélection", "Veuillez sélectionner un contact.")
            return None
        contacts = sorted(self.carnet.get_all_contacts(), key=lambda c: c.nom.lower())
        return contacts[sel[0]]

    def _afficher_details(self):
        c = self._get_selected_contact()
        if not c:
            return

        win = tk.Toplevel(self)
        win.title("Détails")
        win.geometry("360x220")
        win.resizable(False, False)
        win.configure(bg=PANEL)
        win.grab_set()

        cv = tk.Canvas(win, width=360, height=220, bg=PANEL, highlightthickness=0)
        cv.place(x=0, y=0)
        cv.create_rectangle(0, 0, 359, 219, outline=ACCENT, width=2)
        cv.create_rectangle(0, 0, 359, 44, fill=ACCENT, outline="")

        tk.Label(win, text="~ info", font=(MONO, 10, "bold"),
                 fg=CARD, bg=ACCENT).place(x=14, y=12)

        # Nom
        tk.Label(win, text=c.nom, font=(MONO, 15, "bold"),
                 fg=ACCENT, bg=PANEL).place(x=30, y=60)

        # Email avec fond pour lisibilité
        email_frame = tk.Frame(win, bg=BORDER, padx=8, pady=4)
        email_frame.place(x=30, y=105, width=300)
        tk.Label(email_frame, text=c.email, font=(MONO, 10),
                 fg=TEXT, bg=BORDER).pack(anchor="w")

        # Téléphone
        tk.Label(win, text=c.telephone, font=(MONO, 11),
                 fg=MUTED, bg=PANEL).place(x=30, y=150)

        tk.Button(win, text="fermer", font=(MONO, 9, "bold"),
                  bg=ACCENT, fg=CARD, relief="flat", bd=0,
                  padx=20, pady=5, cursor="hand2",
                  command=win.destroy).place(relx=0.5, y=178, anchor="n")

    def _supprimer_contact(self):
        c = self._get_selected_contact()
        if not c:
            return
        if styled_confirm(self, "Confirmer", f"Supprimer '{c.nom}' ?"):
            self.carnet.supprimer_contact(c.email)
            self._refresh_list()

    # ── Formulaire ajout ────────────────────────────────────────────────────

    def _ouvrir_formulaire_ajout(self):
        win = tk.Toplevel(self)
        win.title("Nouveau contact")
        win.geometry("380x320")
        win.resizable(False, False)
        win.configure(bg=PANEL)
        win.grab_set()

        cv = tk.Canvas(win, width=380, height=320, bg=PANEL, highlightthickness=0)
        cv.place(x=0, y=0)
        cv.create_rectangle(0, 0, 379, 319, outline=ACCENT, width=2)
        cv.create_rectangle(0, 0, 379, 44, fill=ACCENT, outline="")

        tk.Label(win, text="+ new contact", font=(MONO, 10, "bold"),
                 fg=CARD, bg=ACCENT).place(x=14, y=12)

        form = tk.Frame(win, bg=PANEL, padx=28)
        form.place(x=0, y=54, width=380)

        entries = {}
        fields = [("nom", "Nom"), ("email", "Email"), ("telephone", "Téléphone")]

        for key, label in fields:
            tk.Label(form, text=f"  {label}", font=(MONO, 8), fg=MUTED,
                     bg=PANEL, anchor="w").pack(fill=tk.X, pady=(8, 0))
            e = tk.Entry(form, font=(MONO, 11), bg=CARD, fg=TEXT,
                         insertbackground=ACCENT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, bd=0)
            e.pack(fill=tk.X, ipady=7)
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

            avant = len(self.carnet.get_all_contacts())
            self.carnet.ajouter_contact(nom, email, telephone)
            if len(self.carnet.get_all_contacts()) > avant:
                self._refresh_list()
                win.destroy()
            else:
                styled_dialog(win, "error", "Doublon", "Email ou téléphone\ndéjà utilisé.")

        tk.Button(form, text="→ ajouter", font=(MONO, 10, "bold"),
                  bg=ACCENT, fg=CARD, activebackground=ACCENT3, activeforeground=CARD,
                  relief="flat", bd=0, pady=9, cursor="hand2",
                  command=valider).pack(fill=tk.X, pady=(16, 0))


if __name__ == "__main__":
    app = App()
    app.mainloop()

    
