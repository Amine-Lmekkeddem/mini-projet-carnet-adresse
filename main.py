from address_book import AddressBook
import re


def menu():

    carnet = AddressBook()

    while True:

        print("\n=== Carnet d'adresse ===")
        print("1. Ajouter un contact")
        print("2. Afficher les contacts")
        print("3. Supprimer un contact")
        print("4. Quitter")

        choix = input("Choisissez une option : ")

        # Ajouter
        if choix == "1":

            # Nom
            while True:

                nom = input("Nom : ").strip()

                if nom != "":
                    break

                print("Le nom est obligatoire.")

            # Email
            while True:

                email = input("Email : ").strip()

                if re.match(
                    r'^[\w\.-]+@[\w\.-]+\.\w+$',
                    email
                ):
                    break

                print("Email invalide.")

            # Téléphone
            while True:

                telephone = input(
                    "Téléphone (10 chiffres) : "
                ).strip()

                if (
                    telephone.isdigit()
                    and len(telephone) == 10
                ):
                    break

                print(
                    "Le téléphone doit contenir 10 chiffres."
                )

            carnet.ajouter_contact(
                nom,
                email,
                telephone
            )

        # Afficher
        elif choix == "2":

            carnet.afficher_contacts()

        # Supprimer
        elif choix == "3":

            identifiant = input(
                "Email ou téléphone : "
            ).strip()

            if identifiant != "":

                carnet.supprimer_contact(
                    identifiant
                )

            else:

                print("Valeur invalide.")

        # Quitter
        elif choix == "4":

            print("Au revoir !")
            break

        else:

            print("Choix invalide.")


if __name__ == "__main__":

    menu()