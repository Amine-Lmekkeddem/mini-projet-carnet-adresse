import re


class Contact:

    def __init__(self, nom, email, telephone):

        # Validation du nom
        assert nom.strip() != "", \
            "Le nom ne peut pas être vide"

        # Validation email
        assert re.match(
            r'^[\w\.-]+@[\w\.-]+\.\w+$',
            email
        ), "Email invalide"

        # Validation téléphone
        assert telephone.isdigit() and len(telephone) == 10, \
            "Le téléphone doit contenir 10 chiffres"

        self.nom = nom.strip()
        self.email = email.strip()
        self.telephone = telephone.strip()

    def __str__(self):

        return (
            f"Nom : {self.nom}\n"
            f"Email : {self.email}\n"
            f"Téléphone : {self.telephone}\n"
        )