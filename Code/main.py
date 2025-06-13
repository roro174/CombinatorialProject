"""
Project of Combinatorial Optimization: ISP problem
Main of the project
Authors:  
    - Fatima Ouchen - 000548670 - MA1-INFO
    - Rodolphe Prévot - 000550332 - MA1-INFO
    - Chahine Mabrouk Bouzouita - 000495542 - MA1-IRCI
Datum: 16/06/2025
"""


import sys
from isp_model import ISPModel
from handle_json import HandleJson



def main():
    """
    Fonction principale du programme.
    """
    if len(sys.argv) != 2:
        print("Usage : python main.py <chemin_du_fichier_json>")
        return

    file_path = sys.argv[1]
    try:
        # Charger les données JSON
        data_handler = HandleJson(file_path)

        # Créer le modèle
        model = ISPModel(data_handler)

        # Résoudre OF1
        print(f"\n--- Résolution de OF1 pour {file_path} ---")
        model.solve_of(True, True)
        # Résoudre OF2
        print(f"\n--- Résolution de OF2 pour {file_path} ---")
        model.solve_of(True, False)


    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    main()
