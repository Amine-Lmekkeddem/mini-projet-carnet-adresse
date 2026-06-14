import re

class Contact:
    def __init__(self, nom, email, telephone):
        assert isinstance(nom, str) and nom.strip() != "", "Le nom doit être une chaîne non vide"
        # assert isinstance(email, str) and "@" in email and "." in email, "Email invalide"
        assert isinstance(email, str) and re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email), "Email invalide"
        assert telephone.isdigit() and len(telephone) == 10 , "Le téléphone doit contenir uniquement des chiffres"

        self.nom = nom
        self.email = email
        self.telephone = telephone

    # def afficher(self):
    #     print(f"Nom: {self.nom}")
    #     print(f"Email: {self.email}")
    #     print(f"Téléphone: {self.telephone}")
    #     print("------------------------")
    
    def __str__(self):
        return f"Nom: {self.nom}" + "\n" + f"Email: {self.email}" + "\n" + f"Téléphone: {self.telephone}" + "\n" 