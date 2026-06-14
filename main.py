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

        if choix == "1":

            # Validation du nom
            while True:
                nom = input("Nom : ")
                if isinstance(nom, str) and nom.strip() != "":
                    break
                print("Le nom doit être une chaîne non vide.")

            # Validation de l'email
            while True:
                email = input("Email : ")

                if isinstance(email, str) and re.match(
                    r'^[\w\.-]+@[\w\.-]+\.\w+$',
                    email
                ):
                    break

                print("Email invalide. Veuillez réessayer.")

            # Validation du téléphone
            while True:
                telephone = input("Téléphone : ")

                if telephone.isdigit() and len(telephone) == 10:
                    break

                print(
                    "Le téléphone doit contenir uniquement 10 chiffres."
                )

            carnet.ajouter_contact(
                nom,
                email,
                telephone
            )

        elif choix == "2":
            carnet.afficher_contacts()

        elif choix == "3":
            nom = input("Nom à supprimer : ")
            carnet.supprimer_contact(nom)

        elif choix == "4":
            print("Au revoir !")
            break

        else:
            print("Choix invalide.")


if __name__ == "__main__":
    menu()