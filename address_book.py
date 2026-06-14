from contact import Contact


class AddressBook:
    def __init__(self):
        self.contacts = []

    def ajouter_contact(self, nom, email, telephone):
        contact = Contact(nom, email, telephone)
        self.contacts.append(contact)
        print("Contact ajouté avec succès !")

    def afficher_contacts(self):
        if not self.contacts:
            print("Aucun contact.")
        else:
            for contact in self.contacts:
                print("------------------------")
                print(contact)

    def supprimer_contact(self, nom):
        for contact in self.contacts:
            if contact.nom.lower() == nom.lower():
                self.contacts.remove(contact)
                print("Contact supprimé.")
                return

        print("Contact non trouvé.")