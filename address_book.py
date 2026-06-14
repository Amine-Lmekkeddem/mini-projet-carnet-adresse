import os
from contact import Contact


class AddressBook:

    def __init__(self, fichier="contacts.txt"):

        self.fichier = fichier

        # Création du fichier
        if not os.path.exists(self.fichier):

            open(self.fichier, "w").close()

    # Lire les contacts
    def get_all_contacts(self):

        contacts = []

        with open(self.fichier, "r", encoding="utf-8") as f:

            for ligne in f:

                ligne = ligne.strip()

                if ligne == "":
                    continue

                nom, email, telephone = ligne.split(";")

                contacts.append(
                    Contact(
                        nom,
                        email,
                        telephone
                    )
                )

        return contacts

    # Ajouter
    def ajouter_contact(self, nom, email, telephone):

        contacts = self.get_all_contacts()

        # Vérification doublons
        for c in contacts:

            if c.email.lower() == email.lower():

                print("Email déjà utilisé.")
                return False

            if c.telephone == telephone:

                print("Téléphone déjà utilisé.")
                return False

        contact = Contact(
            nom,
            email,
            telephone
        )

        with open(self.fichier, "a", encoding="utf-8") as f:

            f.write(
                f"{contact.nom};"
                f"{contact.email};"
                f"{contact.telephone}\n"
            )

        return True

    # Supprimer
    def supprimer_contact(self, email):

        contacts = self.get_all_contacts()

        nouveau = []

        trouve = False

        for c in contacts:

            if c.email.lower() == email.lower():

                trouve = True

            else:

                nouveau.append(c)

        with open(self.fichier, "w", encoding="utf-8") as f:

            for c in nouveau:

                f.write(
                    f"{c.nom};"
                    f"{c.email};"
                    f"{c.telephone}\n"
                )

        return trouve