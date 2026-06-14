import os
import re
from contact import Contact


class AddressBook:

    def __init__(self, fichier="contacts.txt"):
        self.fichier = fichier

        # Création du fichier si inexistant
        if not os.path.exists(self.fichier):
            open(self.fichier, "w").close()

    # Lire tous les contacts
    def get_all_contacts(self):
        contacts = []

        with open(self.fichier, "r", encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()

                if not ligne:
                    continue

                parties = ligne.split(";")

                if len(parties) == 3:
                    nom, email, telephone = parties
                    contacts.append(Contact(nom, email, telephone))

        return contacts

    # Ajouter un contact
    def ajouter_contact(self, nom, email, telephone):

        contacts = self.get_all_contacts()

        # Vérification doublons
        for c in contacts:
            if c.email.lower() == email.strip().lower():
                print("Email déjà utilisé.")
                return False

            if c.telephone == telephone.strip():
                print("Téléphone déjà utilisé.")
                return False

        contact = Contact(nom, email, telephone)

        with open(self.fichier, "a", encoding="utf-8") as f:
            f.write(f"{contact.nom};{contact.email};{contact.telephone}\n")

        print(f"Contact '{contact.nom}' ajouté avec succès.")
        return True

    # Afficher tous les contacts
    def afficher_contacts(self):

        contacts = self.get_all_contacts()

        if not contacts:
            print("Aucun contact enregistré.")
            return

        for contact in contacts:
            print(contact)
            print("-" * 30)

    # Supprimer un contact (email ou téléphone)
    def supprimer_contact(self, identifiant):

        contacts = self.get_all_contacts()

        contact_trouve = None

        for c in contacts:
            if (
                c.email.lower() == identifiant.strip().lower()
                or c.telephone == identifiant.strip()
            ):
                contact_trouve = c
                break

        if contact_trouve is None:
            print(f"Aucun contact trouvé avec '{identifiant}'.")
            return False

        contacts.remove(contact_trouve)

        with open(self.fichier, "w", encoding="utf-8") as f:
            for c in contacts:
                f.write(f"{c.nom};{c.email};{c.telephone}\n")

        print(f"Contact '{contact_trouve.nom}' supprimé avec succès.")
        return True